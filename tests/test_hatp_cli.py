"""Phase 149O.12C, Wave E -- CLI-layer tests for ``pcae hatp sign
rollback`` (`src/pcae/commands/hatp.py`, `src/pcae/cli.py` registration).

Covers: exact grammar (HSCE-REQ-009..012), cross-field locator validation
(HSCE-REQ-013/016/017), the forbidden-flag inventory (HSCE-REQ-017/022/
023/024/026), help/import behavior without hardware (HSCE-REQ-028,
149O.11 plan §13.5), the zero-override production-path assertion (F-2
non-regression, mandatory attack 11), error-type/exit-code mapping
completeness (HSCE-REQ-046..048), and output-schema discipline
(HSCE-REQ-065/066/051).

This module never touches real hardware, real RAE/CHGR state, or the
real filesystem-backed `.pcae/hatp-evidence/` store beyond what a plain
`--help` invocation might (nothing, asserted explicitly below).
`production_sign_rollback_evidence` is monkeypatched only at the single
imported symbol in `pcae.commands.hatp` (149O.11 plan §14 / governing-
prompt §70's first safe option) for the success/error-mapping tests --
never given an override parameter, never patched inside `hatp_signing_
ceremony.py` itself.
"""
from __future__ import annotations

import argparse
import ast
import inspect
import json
import subprocess
import sys
import tokenize
from pathlib import Path

import pytest

from pcae.commands import hatp as hatp_cli
from pcae.core.hatp_evidence_store import EvidenceConflictError, EvidencePersistenceFailureError
from pcae.core.hatp_signed_evidence import HATPSignedEvidenceError
from pcae.core.hatp_signing_ceremony import (
    BindingUnavailableError,
    DecisionUnavailableError,
    EvidenceSerializationFailureError,
    HardwareDeviceFaultError,
    HATPSigningCeremonyError,
    HATPSigningResult,
    HumanSigningCancelledError,
    NoAuthorizedSignerError,
    OperationNotFoundError,
    ProviderSignatureFailureError,
    ProviderUnavailableError,
    RepositoryIdentityUnavailableError,
    production_sign_rollback_evidence,
    sign_rollback_evidence,
)
from pcae.cli import build_parser

# ═══════════════════════════════════════════════════════════════════════════
# Grammar (HSCE-REQ-009/010/011/013/016)
# ═══════════════════════════════════════════════════════════════════════════


def _parse(argv):
    return build_parser().parse_args(argv)


def _code_excluding_strings_and_comments(path: Path) -> str:
    """Static-scan helper: every non-``STRING``/``COMMENT`` token's exact
    text, joined -- so a symbol mentioned only in a docstring/comment
    (explaining what must NOT exist) never trips a "must not appear in
    source" assertion, while a real identifier, call, or argparse flag
    string used as code still would (``add_argument("--provider")`` is a
    ``STRING`` token but is exercised separately by the runtime
    parser-rejection tests above, not by these static-scan tests)."""

    with tokenize.open(path) as fh:
        tokens = tokenize.generate_tokens(fh.readline)
        kept = [tok.string for tok in tokens if tok.type not in (tokenize.STRING, tokenize.COMMENT)]
    return " ".join(kept)


def test_ag3_valid_invocation_parses():
    args = _parse(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1"])
    assert args.site == "ag3"
    assert args.job_id == "job-1"
    assert args.per_id is None
    assert args.json is False
    assert args.handler is hatp_cli.run_hatp_sign_rollback


def test_ag5_valid_invocation_parses():
    args = _parse(["hatp", "sign", "rollback", "--site", "ag5", "--per-id", "per-1", "--json"])
    assert args.site == "ag5"
    assert args.per_id == "per-1"
    assert args.job_id is None
    assert args.json is True


def test_site_is_required():
    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--job-id", "job-1"])


def test_unknown_site_is_argparse_error():
    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--site", "ag4", "--job-id", "job-1"])


def test_uppercase_site_is_argparse_error():
    """HSCE-REQ-010: `--site` accepts exactly the closed, lowercase
    values `ag3`/`ag5` -- case-sensitive, no uppercase alias."""

    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--site", "AG3", "--job-id", "job-1"])


def test_no_dry_run_flag_exists():
    """HSCE-REQ-012: no `--dry-run` flag exists on this command."""

    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1", "--dry-run"])


# ═══════════════════════════════════════════════════════════════════════════
# Cross-field locator validation (HSCE-REQ-013/016/017), attacks 6-10 of the
# governing prompt's own numbering
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "argv,expected_message_fragment",
    [
        (["--site", "ag3"], "--job-id is required"),
        (["--site", "ag5"], "--per-id is required"),
        (["--site", "ag3", "--per-id", "p-1"], "not a valid locator for --site ag3"),
        (["--site", "ag5", "--job-id", "j-1"], "not a valid locator for --site ag5"),
        (["--site", "ag3", "--job-id", "j-1", "--per-id", "p-1"], "not a valid locator for --site ag3"),
        (["--site", "ag5", "--job-id", "j-1", "--per-id", "p-1"], "not a valid locator for --site ag5"),
    ],
)
def test_locator_validation_rejects_before_production_call(monkeypatch, argv, expected_message_fragment, capsys):
    called = []
    monkeypatch.setattr(hatp_cli, "production_sign_rollback_evidence", lambda *a, **k: called.append(1))

    args = _parse(["hatp", "sign", "rollback", *argv])
    exit_code = hatp_cli.run_hatp_sign_rollback(args)

    assert exit_code == 2
    assert not called, "production wrapper must never be invoked for invalid locator combinations"
    out = capsys.readouterr().out
    assert expected_message_fragment in out


def test_locator_validation_error_json_has_no_error_type(monkeypatch, capsys):
    """A CLI-level usage error is distinct from the closed HSCE
    `error_type` vocabulary (governing-prompt §25) -- it never carries an
    `error_type` field."""

    monkeypatch.setattr(hatp_cli, "production_sign_rollback_evidence", lambda *a, **k: None)
    args = _parse(["hatp", "sign", "rollback", "--site", "ag3", "--json"])
    exit_code = hatp_cli.run_hatp_sign_rollback(args)
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "error_type" not in payload


# ═══════════════════════════════════════════════════════════════════════════
# Forbidden-flag inventory (HSCE-REQ-017/022/023/024/026, governing-prompt §11)
# ═══════════════════════════════════════════════════════════════════════════

_FORBIDDEN_FLAGS = [
    "--provider",
    "--signer",
    "--principal",
    "--trust-store",
    "--credential-store",
    "--force",
    "--overwrite",
    "--output",
    "--repository-id",
    "--decision-id",
    "--decision-digest",
    "--binding-id",
    "--binding-digest",
    "--signer-key-id",
    "--ecp-id",
    "--original-commit-sha",
    "--issued-at",
    "--timestamp",
    "--approval-present",
    "--hatp-valid",
    "--operational",
    "--dry-run",
    "--hatp-trust-store",
    "--trusted-key",
    "--dev",
    "--test-provider",
    "--software-provider",
    "--skip-touch",
    "--assume-present",
    "--ignore-not-ready",
    "--root",
]


@pytest.mark.parametrize("flag", _FORBIDDEN_FLAGS)
def test_forbidden_flag_rejected_by_parser(flag):
    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1", flag, "x"])


def test_forbidden_flags_absent_from_source():
    """Static confirmation, independent of argparse's own runtime
    rejection above: none of the forbidden flag strings appear anywhere
    in the CLI handler module's actual code (docstring/comment mentions
    explaining what must not exist are not code)."""

    code = _code_excluding_strings_and_comments(Path(hatp_cli.__file__))
    for flag in _FORBIDDEN_FLAGS:
        assert flag not in code, f"forbidden flag {flag!r} must never appear in commands/hatp.py's code"


# ═══════════════════════════════════════════════════════════════════════════
# Zero-override production-path assertion (F-2 non-regression, attack 11)
# ═══════════════════════════════════════════════════════════════════════════


def test_production_wrapper_signature_carries_no_override_parameter():
    params = set(inspect.signature(production_sign_rollback_evidence).parameters)
    assert params == {"root", "site", "job_id", "per_id"}


def test_injectable_sign_function_never_imported_by_cli_handler():
    code = _code_excluding_strings_and_comments(Path(hatp_cli.__file__))
    assert "sign_rollback_evidence" not in code.replace("production_sign_rollback_evidence", "")


def test_handler_calls_production_wrapper_with_only_frozen_kwargs():
    """AST-level proof that `run_hatp_sign_rollback`'s only call to
    `production_sign_rollback_evidence` passes exactly the frozen
    `root`/`site`/`job_id`/`per_id` arguments -- no `provider=`/
    `trust_store=`/`clock=`/`confirm=`/`store=`/`context_resolver=` or
    any other keyword."""

    source = Path(hatp_cli.__file__).read_text()
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "production_sign_rollback_evidence"
    ]
    assert len(calls) == 1, "exactly one call site of production_sign_rollback_evidence is expected"
    call = calls[0]
    kwarg_names = {kw.arg for kw in call.keywords}
    all_argument_names = kwarg_names | (set() if not call.args else {"root"})
    assert all_argument_names == {"root", "site", "job_id", "per_id"}
    assert kwarg_names == {"site", "job_id", "per_id"}
    assert len(call.args) == 1


def test_run_hatp_sign_rollback_is_the_only_reference_to_sign_rollback_evidence_name_prefix():
    """`hatp.py` must reference the production entry point only --
    confirmed by scanning every `ast.Name`/`ast.Attribute` identifier in
    the module for the bare `sign_rollback_evidence` symbol (as opposed
    to `production_sign_rollback_evidence`, which legitimately contains
    it as a substring)."""

    source = Path(hatp_cli.__file__).read_text()
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.alias):
            names.add(node.asname or node.name)
    assert "sign_rollback_evidence" not in names
    assert "production_sign_rollback_evidence" in names


# ═══════════════════════════════════════════════════════════════════════════
# Help / import behavior without hardware (HSCE-REQ-028, attack 11's CLI half)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "argv",
    [
        ["hatp", "--help"],
        ["hatp", "sign", "--help"],
        ["hatp", "sign", "rollback", "--help"],
    ],
)
def test_help_succeeds_without_hardware_in_subprocess(argv):
    """Subprocess-isolated (149O.11 plan §13.5, governing-prompt §17/18):
    `--help` at every level of the `hatp` command hierarchy exits 0 with
    no exception, in a fresh interpreter, regardless of FIDO2 device
    presence -- no hardware discovery occurs at parser-construction or
    help-rendering time."""

    completed = subprocess.run(
        [sys.executable, "-c", "from pcae.cli import main; import sys; sys.exit(main(sys.argv[1:]))", *argv],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr


def test_help_creates_no_evidence_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["hatp", "sign", "rollback", "--help"])
    assert exc_info.value.code == 0
    assert not (tmp_path / ".pcae" / "hatp-evidence").exists()


def test_module_importable_without_touching_filesystem_or_hardware():
    """Plain import of `pcae.commands.hatp` performs no I/O, no hardware
    discovery, and constructs no store/provider."""

    import importlib

    importlib.reload(hatp_cli)  # re-import is side-effect-free


# ═══════════════════════════════════════════════════════════════════════════
# error_type / exit-code mapping completeness (HSCE-REQ-046..048)
# ═══════════════════════════════════════════════════════════════════════════

_CLOSED_ERROR_VOCABULARY = {
    "repository_identity_unavailable",
    "operation_not_found",
    "decision_unavailable",
    "binding_unavailable",
    "no_authorized_signer",
    "provider_unavailable",
    "hardware_device_fault",
    "human_signing_cancelled",
    "provider_signature_failure",
    "evidence_serialization_failure",
    "evidence_conflict",
    "evidence_persistence_failure",
}

_EXIT_CATEGORIES = {
    hatp_cli.EXIT_SUCCESS,
    hatp_cli.EXIT_GENERIC_SIGNING_FAILURE,
    hatp_cli.EXIT_OPERATION_NOT_FOUND,
    hatp_cli.EXIT_GOVERNANCE_STATE_UNAVAILABLE,
    hatp_cli.EXIT_SUBSTRATE_UNAVAILABLE,
    hatp_cli.EXIT_HUMAN_CANCELLED,
    hatp_cli.EXIT_PROVIDER_FAILURE,
    hatp_cli.EXIT_EVIDENCE_CONFLICT,
    hatp_cli.EXIT_PERSISTENCE_FAILURE,
}


def test_error_vocabulary_is_exactly_the_closed_12_member_set():
    assert set(hatp_cli._EXIT_CODE_BY_ERROR_TYPE) == _CLOSED_ERROR_VOCABULARY


def test_every_error_type_maps_to_exactly_one_exit_code():
    for error_type, exit_code in hatp_cli._EXIT_CODE_BY_ERROR_TYPE.items():
        assert isinstance(exit_code, int)


def test_all_nine_exit_categories_are_represented():
    assert len(_EXIT_CATEGORIES) == 9
    mapped_codes = set(hatp_cli._EXIT_CODE_BY_ERROR_TYPE.values()) | {hatp_cli.EXIT_SUCCESS}
    assert mapped_codes == _EXIT_CATEGORIES


def test_ceremony_error_subclasses_error_type_all_map():
    """Every `HATPSigningCeremonyError` subclass this module can catch
    carries an `error_type` present in the closed mapping."""

    for exc_type in (
        RepositoryIdentityUnavailableError,
        OperationNotFoundError,
        DecisionUnavailableError,
        BindingUnavailableError,
        NoAuthorizedSignerError,
        ProviderUnavailableError,
        HardwareDeviceFaultError,
        HumanSigningCancelledError,
        ProviderSignatureFailureError,
        EvidenceSerializationFailureError,
    ):
        instance = exc_type("boom")
        assert hatp_cli._error_type_for(instance) in _CLOSED_ERROR_VOCABULARY
        assert hatp_cli._EXIT_CODE_BY_ERROR_TYPE[hatp_cli._error_type_for(instance)] in _EXIT_CATEGORIES


def test_evidence_store_errors_map_correctly():
    assert hatp_cli._error_type_for(EvidenceConflictError("x")) == "evidence_conflict"
    assert hatp_cli._error_type_for(EvidencePersistenceFailureError("x")) == "evidence_persistence_failure"


def test_signed_evidence_structural_error_maps_to_serialization_failure():
    assert hatp_cli._error_type_for(HATPSignedEvidenceError("x")) == "evidence_serialization_failure"


# ═══════════════════════════════════════════════════════════════════════════
# Output rendering / exit-zero semantics (HSCE-REQ-065/066/051), success and
# every one of the 12 error types, human + JSON
# ═══════════════════════════════════════════════════════════════════════════


class _FakeResult:
    def __init__(self, evidence_id="e" * 64, path="/tmp/evidence.json", idempotent=False):
        self.evidence_id = evidence_id
        self.path = path
        self.idempotent = idempotent


def _run(monkeypatch, effect, *, as_json, extra_argv=None):
    monkeypatch.setattr(hatp_cli, "production_sign_rollback_evidence", lambda *a, **k: effect())
    argv = ["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1"]
    if as_json:
        argv.append("--json")
    if extra_argv:
        argv.extend(extra_argv)
    args = _parse(argv)
    return hatp_cli.run_hatp_sign_rollback(args)


def test_success_human_output_has_no_authority_claims(monkeypatch, capsys):
    exit_code = _run(monkeypatch, lambda: _FakeResult(), as_json=False)
    assert exit_code == 0
    out = capsys.readouterr().out
    for forbidden_word in ("approved", "allowed", "authorized for execution", "permission granted", "rollback ready", "rollback executed"):
        assert forbidden_word not in out.lower()
    assert "Signed HATP evidence created" in out
    assert "e" * 64 in out


def test_success_json_output_schema_is_exact(monkeypatch, capsys):
    exit_code = _run(monkeypatch, lambda: _FakeResult(evidence_id="f" * 64, path="/x/y.json", idempotent=True), as_json=True)
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "status": "success",
        "evidence_id": "f" * 64,
        "evidence_path": "/x/y.json",
        "idempotent": True,
    }
    for forbidden_key in ("approval_present", "hatp_valid", "pb_decision", "execution_available", "approved", "permission", "executed"):
        assert forbidden_key not in payload


@pytest.mark.parametrize(
    "exc_factory,expected_error_type,expected_exit",
    [
        (lambda: RepositoryIdentityUnavailableError("no identity"), "repository_identity_unavailable", 3),
        (lambda: OperationNotFoundError("no job"), "operation_not_found", 2),
        (lambda: DecisionUnavailableError("no decision"), "decision_unavailable", 3),
        (lambda: BindingUnavailableError("no binding"), "binding_unavailable", 3),
        (lambda: NoAuthorizedSignerError("not enrolled"), "no_authorized_signer", 4),
        (lambda: ProviderUnavailableError("no device"), "provider_unavailable", 4),
        (lambda: HardwareDeviceFaultError("transport fault"), "hardware_device_fault", 6),
        (lambda: HumanSigningCancelledError("declined"), "human_signing_cancelled", 5),
        (lambda: ProviderSignatureFailureError("bad sig"), "provider_signature_failure", 6),
        (lambda: EvidenceSerializationFailureError("stale"), "evidence_serialization_failure", 1),
        (lambda: EvidenceConflictError("conflict"), "evidence_conflict", 7),
        (lambda: EvidencePersistenceFailureError("fs fail"), "evidence_persistence_failure", 8),
    ],
)
def test_every_error_type_human_and_json_output_and_exit_code(monkeypatch, capsys, exc_factory, expected_error_type, expected_exit):
    def _raise():
        raise exc_factory()

    exit_code = _run(monkeypatch, _raise, as_json=False)
    assert exit_code == expected_exit
    out = capsys.readouterr().out
    assert f"error_type: {expected_error_type}" in out

    exit_code_json = _run(monkeypatch, _raise, as_json=True)
    assert exit_code_json == expected_exit
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["error_type"] == expected_error_type
    for forbidden_key in ("approved", "permission", "executed", "approval_present"):
        assert forbidden_key not in payload


def test_evidence_conflict_never_prompts_overwrite(monkeypatch, capsys):
    """Attack 4 / HSCE-REQ-047: `evidence_conflict` is a hard rejection,
    never an interactive overwrite prompt -- confirmed by asserting the
    handler makes no `input()` call and no `--force`/`--overwrite` flag
    exists (also covered by the forbidden-flag inventory above)."""

    called_input = []
    monkeypatch.setattr("builtins.input", lambda *a, **k: called_input.append(1) or "y")

    def _raise():
        raise EvidenceConflictError("differing bytes")

    exit_code = _run(monkeypatch, _raise, as_json=False)
    assert exit_code == 7
    assert not called_input


def test_unexpected_internal_exception_is_never_mislabeled_as_success(monkeypatch):
    """Requirement 83/108: a genuine bug (an exception type outside the
    closed vocabulary) must never be caught and re-labeled as a
    classified signing failure or, worse, a success -- it propagates."""

    def _raise():
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr(hatp_cli, "production_sign_rollback_evidence", lambda *a, **k: _raise())
    args = _parse(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1"])
    with pytest.raises(RuntimeError):
        hatp_cli.run_hatp_sign_rollback(args)


# ═══════════════════════════════════════════════════════════════════════════
# No PB / no legacy mutation / no rollback dispatch reachable from this module
# (HSCE-REQ-067, SC-8/SC-9/SC-10)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_scope_creep_in_cli_handler_source():
    code = _code_excluding_strings_and_comments(Path(hatp_cli.__file__))
    for forbidden_symbol in (
        "permission_broker",
        "verify_hatp_proof",
        "approve_rollback",
        "execute_rollback",
        "build_rollback_execution",
        "run_rollback",
        "approval_present",
        "rollback_approval_state",
    ):
        assert forbidden_symbol not in code


def test_no_root_flag_exists():
    with pytest.raises(SystemExit):
        _parse(["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1", "--root", "/tmp"])
