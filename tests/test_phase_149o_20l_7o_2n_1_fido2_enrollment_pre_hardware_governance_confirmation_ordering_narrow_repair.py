"""Phase 149O.20L.7O.2N.1 -- FIDO2 Enrollment Pre-Hardware Governance
Confirmation Ordering Narrow Repair.

Repairs Blocking finding B-149O.20L.7O.2N-1, independently established
by Phase 149O.20L.7O.2N from current production source:
`scripts/hatp_hardware_credential_admin.py::_cmd_enroll` ran the real
FIDO2 `makeCredential` ceremony (`_run_enrollment_ceremony`,
`Fido2HardwareProvider.enroll_credential()`) BEFORE the governance
confirmation gate (`_prompt_confirm`/`--assume-yes`) was even checked --
a declined confirmation could not prevent a real hardware effect that
had already happened.

Repair: the confirmation gate now runs first, using only prospective,
non-secret operation parameters (`repository_root`, `enrollment_reference`,
the fixed provider profile constant, the operation name) --
`_describe_prospective_enrollment` -- since a real `signer_key_id`/
`public_key` does not exist until a real ceremony succeeds and cannot be
truthfully bound to a pre-hardware confirmation. `--preview` was
redefined the same way: it previously ran the real ceremony
unconditionally with zero confirmation of any kind (the same root
defect, just with an absent gate rather than a too-late one); it now
renders the identical pre-hardware description and never touches
hardware.

This suite:

  1. reproduces the pre-repair defect against the preserved fixed
     Git checkpoint (this phase's own true phase-entry commit);
  2. proves the post-repair event ordering and the central
     zero-effect invariant on a declined confirmation;
  3. proves the narrow blast radius: every other HMIC v1.7-bound
     production file is untouched (byte-identical), while this one
     script's `implementation_scope_digest` contribution provably
     changes (documented HMIC consequence, not implemented here).

Every test uses a synthetic/mock FIDO2 provider seam or `tmp_path`; no
test touches real hardware, installs `fido2`, or connects to hac-dell.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

fido2 = pytest.importorskip("fido2")

from pcae.core import hatp_hardware_credential_admin as hw_admin
from pcae.core.hatp_fido2_provider import EnrolledFido2Credential
from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_hardware_credential_admin.py"

#: true phase-entry commit for 149O.20L.7O.2N.1 -- the tip of
#: `main` immediately before this phase's own first commit, preserving
#: the pre-repair defect for independent verification (§29 of the
#: governing prompt).
_PRE_REPAIR_CHECKPOINT = "cbcbcc0cbb30e109329043f1e7fbb80d37a8fd2d"

_SIGNER_KEY_ID = "aa" * 16
_PUBLIC_KEY_HEX = "bb" * 20


def _git(args, cwd=_REPO_ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _load_module_from_source(source: str, *, name: str):
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(_SCRIPT_PATH), "exec"), module.__dict__)
    return module


def _load_current_script_module():
    spec = importlib.util.spec_from_file_location("hatp_hw_admin_2n1_current", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_enrolled():
    return EnrolledFido2Credential(
        credential_id_hex=_SIGNER_KEY_ID,
        algorithm="ES256",
        public_key_hex=_PUBLIC_KEY_HEX,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
    )


def _bind_store(func, store_root: Path):
    def wrapper(*args, **kwargs):
        kwargs.setdefault("_store_root", store_root)
        return func(*args, **kwargs)

    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# 1. Pre-repair defect reproduction against the fixed checkpoint.
# ═══════════════════════════════════════════════════════════════════════════


def test_pre_repair_checkpoint_reproduces_provider_before_confirmation(tmp_path, monkeypatch):
    pre_source = _git(["show", f"{_PRE_REPAIR_CHECKPOINT}:scripts/hatp_hardware_credential_admin.py"])
    module = _load_module_from_source(pre_source, name="hatp_hw_admin_2n1_pre_repair_checkpoint")

    store = tmp_path / "hwstore"
    store.mkdir()
    monkeypatch.setattr(module, "register_credential", _bind_store(hw_admin.register_credential, store))
    monkeypatch.setattr(module, "preview_register_credential", _bind_store(hw_admin.preview_register_credential, store))

    events = []
    monkeypatch.setattr(module, "_run_enrollment_ceremony", lambda **kw: events.append("PROVIDER_ENROLLMENT_CALLED") or _fake_enrolled())
    monkeypatch.setattr(module, "_prompt_confirm", lambda desc: events.append("CONFIRMATION_CHECKED") or False)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    code = module.main(["enroll", "--repository-root", str(repo_root), "--enrollment-reference", "CHGR-PRE"])

    assert code == 1
    assert events == ["PROVIDER_ENROLLMENT_CALLED", "CONFIRMATION_CHECKED"], (
        "pre-repair checkpoint must reproduce the defect: provider enrollment happens "
        "before the confirmation gate is even checked"
    )
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


# ═══════════════════════════════════════════════════════════════════════════
# 2. Post-repair ordering and zero-effect invariant (current source).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    root = tmp_path / "hwstore"
    root.mkdir()
    return root


@pytest.fixture()
def script(monkeypatch: pytest.MonkeyPatch, store: Path):
    module = _load_current_script_module()
    monkeypatch.setattr(module, "register_credential", _bind_store(hw_admin.register_credential, store))
    monkeypatch.setattr(module, "preview_register_credential", _bind_store(hw_admin.preview_register_credential, store))
    monkeypatch.setattr(module, "preview_revoke_credential", _bind_store(hw_admin.preview_revoke_credential, store))
    return module


def test_post_repair_confirmation_checked_before_provider_enrollment(script, monkeypatch, tmp_path, store):
    events = []
    monkeypatch.setattr(script, "_run_enrollment_ceremony", lambda **kw: events.append("PROVIDER_ENROLLMENT_CALLED") or _fake_enrolled())
    monkeypatch.setattr(script, "_prompt_confirm", lambda desc: events.append("CONFIRMATION_CHECKED") or True)

    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-POST"])

    assert code == 0
    assert events == ["CONFIRMATION_CHECKED", "PROVIDER_ENROLLMENT_CALLED"]
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is not None


def test_post_repair_declined_confirmation_zero_provider_zero_writer(script, monkeypatch, tmp_path, store):
    events = []
    monkeypatch.setattr(script, "_run_enrollment_ceremony", lambda **kw: events.append("PROVIDER_ENROLLMENT_CALLED") or _fake_enrolled())
    real_register = hw_admin.register_credential
    write_calls = []

    def _register(*args, **kwargs):
        write_calls.append(1)
        return real_register(*args, **kwargs)

    monkeypatch.setattr(script, "register_credential", _bind_store(_register, store))
    monkeypatch.setattr(script, "_prompt_confirm", lambda desc: events.append("CONFIRMATION_CHECKED") or False)

    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-DECLINE"])

    assert code == 1
    assert events == ["CONFIRMATION_CHECKED"], "no provider call may occur once confirmation is declined"
    assert write_calls == []
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


def test_preview_mode_never_calls_provider(script, monkeypatch, tmp_path, store):
    monkeypatch.setattr(script, "_run_enrollment_ceremony", lambda **kw: (_ for _ in ()).throw(AssertionError("preview must not touch hardware")))
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-PREVIEW", "--preview"])
    assert code == 0
    assert hw_admin.HATPHardwareCredentialStore(_test_only_root=store).lookup_credential(_SIGNER_KEY_ID) is None


# ═══════════════════════════════════════════════════════════════════════════
# 3. Narrow blast radius: everything else byte-identical; this script's
#    scope-digest contribution provably changes.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "path",
    [
        # "src/pcae/core/hatp_hardware_credential_admin.py" and
        # "src/pcae/core/hatp_hardware_credentials.py" intentionally
        # excluded as of Phase 149O.20L.7O.2N.13, which legitimately
        # changed both (protocol_name vocabulary widening + duplicated-
        # validator centralization, NBF-149O.20L.7O.2N.12-2's repair) --
        # see that phase's own dedicated test module for coverage.
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_piv_provider.py",
        "src/pcae/core/hatp_providers.py",
        "scripts/hatp_principal_signer_admin.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
        "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
        "src/pcae/core/hatp_mandatory_certification.py",
    ],
)
def test_all_other_hmic_bound_files_byte_identical_across_2n_1(path):
    pre = _git(["show", f"{_PRE_REPAIR_CHECKPOINT}:{path}"])
    current = (_REPO_ROOT / path).read_text(encoding="utf-8")
    assert pre == current, f"{path} must remain byte-identical -- this repair touches only the admin script"


def test_repaired_script_diverges_from_pre_repair_checkpoint():
    pre = _git(["show", f"{_PRE_REPAIR_CHECKPOINT}:scripts/hatp_hardware_credential_admin.py"])
    current = _SCRIPT_PATH.read_text(encoding="utf-8")
    assert pre != current, "the repair is expected to change this file's bytes"


def test_repaired_script_per_file_digest_changes_from_pre_repair_checkpoint():
    """Standalone proof of this phase's §24/§25 HMIC consequence
    determination: this script's own per-file SHA-256 contribution to
    `derive_implementation_scope_digest` (HMIC-REQ-057/058) changes as a
    direct result of the repair -- without invoking the real digest
    derivation (which requires all 38 frozen files present and would
    reach outside this task's allowed-files scope). This alone is
    sufficient: the two-level digest construction means any single
    per-file digest change propagates to the overall
    `implementation_scope_digest`."""

    pre = _git(["show", f"{_PRE_REPAIR_CHECKPOINT}:scripts/hatp_hardware_credential_admin.py"])
    current = _SCRIPT_PATH.read_text(encoding="utf-8")
    pre_digest = hashlib.sha256(pre.encode("utf-8")).hexdigest()
    current_digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    assert pre_digest != current_digest


# ═══════════════════════════════════════════════════════════════════════════
# 4. Successful synthetic sequence, one-ceremony invariant, retry
#    non-regression -- re-derived directly, not merely inherited from
#    `tests/test_hatp_hardware_credential_admin_script.py`.
# ═══════════════════════════════════════════════════════════════════════════


def test_successful_enrollment_full_sequence(script, monkeypatch, tmp_path, store):
    events = []
    monkeypatch.setattr(script, "_run_enrollment_ceremony", lambda **kw: events.append("PROVIDER_ENROLLMENT") or _fake_enrolled())
    monkeypatch.setattr(script, "_prompt_confirm", lambda desc: events.append("CONFIRMATION_CHECKED") or True)
    real_register = hw_admin.register_credential
    monkeypatch.setattr(
        script,
        "register_credential",
        _bind_store(lambda *a, **kw: (events.append("REGISTER_CREDENTIAL"), real_register(*a, **kw))[1], store),
    )

    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-SUCCESS"])

    assert code == 0
    assert events == ["CONFIRMATION_CHECKED", "PROVIDER_ENROLLMENT", "REGISTER_CREDENTIAL"]


def test_persistence_retry_never_calls_provider_a_second_time(script, monkeypatch, tmp_path, store):
    ceremony_calls = []
    monkeypatch.setattr(script, "_run_enrollment_ceremony", lambda **kw: ceremony_calls.append(1) or _fake_enrolled())

    real_register = hw_admin.register_credential
    write_attempts = []

    def _flaky(*, repository_root, evidence):
        write_attempts.append(evidence)
        if len(write_attempts) == 1:
            raise hw_admin.HardwareCredentialStoreUnavailableError("simulated transient failure")
        return real_register(repository_root=repository_root, evidence=evidence, _store_root=store)

    monkeypatch.setattr(script, "register_credential", _flaky)
    code = script.main(["enroll", "--repository-root", str(tmp_path), "--enrollment-reference", "CHGR-RETRY", "--assume-yes"])

    assert code == 0
    assert len(ceremony_calls) == 1, "at most one makeCredential ceremony per invocation"
    assert len(write_attempts) == 2
    assert write_attempts[0] is write_attempts[1]


def test_no_caller_supplied_credential_identity_flag_exists(script):
    enroll_actions = {a.dest for a in script._build_parser()._subparsers._group_actions[0].choices["enroll"]._actions}
    assert not (enroll_actions & {"credential_id", "public_key", "public_key_hex", "signer_key_id"})


def test_revoke_subcommand_source_unchanged_by_this_repair():
    """Revoke is not part of this repair's scope; its handler source
    text is unchanged since the pre-repair checkpoint."""

    pre_source = _git(["show", f"{_PRE_REPAIR_CHECKPOINT}:scripts/hatp_hardware_credential_admin.py"])
    current_source = _SCRIPT_PATH.read_text(encoding="utf-8")

    def _extract(text: str) -> str:
        start = text.index("def _cmd_revoke(")
        end = text.index("\ndef _build_parser(")
        return text[start:end]

    assert _extract(pre_source) == _extract(current_source)
