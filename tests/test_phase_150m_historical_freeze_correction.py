"""Execute the repaired ORIGINAL assertions against real immutable Git trees.

Only synthetic repositories are mutated. No historical objects are rewritten.
These tests check boundary correctness, not deployed generation provenance.
"""
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("150i_phase_report_rehydration_identity_repair", "test_runtime_and_product_boundaries_are_untouched",
     "93424bea862aab27fcb2401a5e83e28481b1929a", "841c61e13b20132896b4b9674e4add58544364ac"),
    ("150j_rehydration_identity_repair_iv", "test_this_iv_has_zero_production_and_contract_delta",
     "841c61e13b20132896b4b9674e4add58544364ac", "c90254a2648e4afb263373fd4aff2afb48946e2e"),
    ("150k_provenance_certification_link_repair", "test_architectural_stop_changes_no_production_or_contracts",
     "c90254a2648e4afb263373fd4aff2afb48946e2e", "8c998d2b2654e45e189bc3bfda57c7b6ecd71d7f"),
)


def load_case(case):
    path = ROOT / f"tests/test_phase_{case[0]}.py"
    spec = importlib.util.spec_from_file_location("freeze_witness_" + case[0], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, getattr(module, case[1])


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root, message):
    git(root, "add", "--all")
    git(root, "-c", "user.name=Freeze fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture(params=CASES, ids=["150I", "150J", "150K"])
def frozen(request, tmp_path, monkeypatch):
    module, assertion = load_case(request.param)
    git(tmp_path, "init", "-q")
    for relative in ("docs/contracts/frozen.md", "src/pcae/core/hpac_foundation.py"):
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Version: 1.0\nProtected historical body\n", encoding="utf-8")
    entry = commit(tmp_path, "historical entry")
    (tmp_path / "evidence.txt").write_text("phase evidence", encoding="utf-8")
    end = commit(tmp_path, "historical closure")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "ENTRY", entry)
    monkeypatch.setattr(module, "PHASE_END", end)
    return tmp_path, module, assertion


def test_legitimate_future_addition_does_not_change_frozen_phase(frozen):
    root, _, assertion = frozen
    assertion()
    (root / "docs/contracts/later-authorized-contract.md").write_text("New governed contract\n")
    commit(root, "later authorized contract")
    assertion()  # CURRENT HEAD is deliberately different; phase endpoint is fixed.
    (root / "docs/contracts/frozen.md").write_text("Later governed revision\n")
    commit(root, "later authorized version evolution")
    assertion()


@pytest.mark.parametrize("mutation", ["body", "delete", "symlink", "same-version",
                                     "scope-contraction", "scope-substitution", "forbidden-addition"])
@pytest.mark.parametrize("relative", ["docs/contracts/frozen.md", "src/pcae/core/hpac_foundation.py"])
def test_original_assertion_rejects_protected_historical_mutation(frozen, mutation, relative):
    root, module, assertion = frozen
    p = root / relative
    if mutation == "body":
        p.write_text("Changed frozen content\n")
    elif mutation == "delete":
        p.unlink()
    elif mutation == "symlink":
        p.unlink()
        p.symlink_to("../../evidence.txt")
    elif mutation == "same-version":
        p.write_text("Version: 1.0\nSame version, different protected body\n")
    elif mutation == "scope-contraction":
        p.write_text("Version: 1.0\n")
    elif mutation == "scope-substitution":
        p.rename(p.with_name("replacement" + p.suffix))
    else:
        name = "hpac_pawa_helper_unauthorized.py" if p.suffix == ".py" else "unauthorized.md"
        p.with_name(name).write_text("Unauthorized protected phase scope growth\n")
    module.PHASE_END = commit(root, "injected forbidden HISTORICAL endpoint")
    with pytest.raises(AssertionError):
        assertion()


@pytest.mark.parametrize("case", CASES)
def test_boundaries_are_real_completed_phase_commits_and_original_assertion_passes(case):
    module, assertion = load_case(case)
    assert (module.ENTRY, module.PHASE_END) == case[2:]
    for oid in case[2:]:
        assert git(ROOT, "rev-parse", oid + "^{commit}") == oid
    subprocess.run(["git", "merge-base", "--is-ancestor", case[2], case[3]], cwd=ROOT, check=True)
    assertion()
