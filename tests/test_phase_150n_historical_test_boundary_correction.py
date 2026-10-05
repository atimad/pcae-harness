"""Run original L/M assertions against pinned real and isolated synthetic history."""
import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "5a79d079ffcfb53bb0d46477958c99c877750579"
CASES = (
    ("150l_generation_provenance_architecture", "test_zero_production_delta_from_fixed_entry",
     "8c998d2b2654e45e189bc3bfda57c7b6ecd71d7f", "944228ac9cdbe91711c5e4c32190640cec467068"),
    ("150m_architecture_revalidation", "test_no_production_contract_or_lifecycle_consumer_delta",
     "944228ac9cdbe91711c5e4c32190640cec467068", ENTRY),
)


def load(case):
    spec = importlib.util.spec_from_file_location(case[0], ROOT / f"tests/test_phase_{case[0]}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, getattr(module, case[1])


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def commit(root, message):
    git(root, "add", "--all")
    git(root, "-c", "user.name=Boundary fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture(params=CASES, ids=["150L", "150M"])
def history(request, tmp_path, monkeypatch):
    module, assertion = load(request.param)
    git(tmp_path, "init", "-q")
    source = tmp_path / "src/pcae/core/existing.py"
    source.parent.mkdir(parents=True)
    source.write_text("# Existing historical production source\n")
    entry = commit(tmp_path, "historical entry")
    (tmp_path / "evidence.txt").write_text("Historical phase evidence\n")
    end = commit(tmp_path, "historical closure")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "ENTRY", entry)
    monkeypatch.setattr(module, "PHASE_END", end)
    return tmp_path, module, assertion


def test_future_production_module_and_schema_strings_do_not_change_history(history):
    root, module, assertion = history
    assertion()
    future = root / "src/pcae/core/future_gcp_pure_model.py"
    future.write_text("SCHEMA = 'gcp-generation/1.0'\nTERMINAL = 'gcp-terminal/1.0'\n")
    commit(root, "future authorized implementation")
    assertion()
    (root / "src/pcae/core/existing.py").write_text("# future revision gcp-generation/1.0\n")
    assertion()  # Even uncommitted current source is outside the historical tree.
    if "150l" in module.__name__:
        contract = root / "docs/contracts/future.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("Future authorized contract\n")
        commit(root, "future authorized contract")
        module.test_existing_contracts_unchanged()


@pytest.mark.parametrize("mutation", ["body", "addition", "deletion", "rename", "symlink"])
def test_historical_production_violation_is_rejected(history, mutation):
    root, module, assertion = history
    source = root / "src/pcae/core/existing.py"
    if mutation == "body":
        source.write_text("# Unauthorized historical change\n")
    elif mutation == "addition":
        source.with_name("unauthorized.py").write_text("# Unauthorized historical addition\n")
    elif mutation == "deletion":
        source.unlink()
    elif mutation == "rename":
        source.rename(source.with_name("substitution.py"))
    else:
        source.unlink()
        source.symlink_to("../../../evidence.txt")
    module.PHASE_END = commit(root, "historical violation fixture")
    with pytest.raises(AssertionError):
        assertion()


@pytest.mark.parametrize("schema", ["gcp-generation/1.0", "gcp-terminal/1.0"])
def test_m_historical_source_scan_rejects_schema_even_with_zero_diff(tmp_path, monkeypatch, schema):
    module, assertion = load(CASES[1])
    git(tmp_path, "init", "-q")
    source = tmp_path / "src/pcae/core/model.py"
    source.parent.mkdir(parents=True)
    source.write_text(f"SCHEMA = '{schema}'\n")
    endpoint = commit(tmp_path, "prohibited historical snapshot fixture")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "ENTRY", endpoint)
    monkeypatch.setattr(module, "PHASE_END", endpoint)
    assert git(tmp_path, "diff", endpoint, endpoint, "--", "src/pcae") == ""
    with pytest.raises(AssertionError):
        assertion()


@pytest.mark.parametrize("case", CASES)
def test_real_endpoints_ancestry_phase_commit_inventory_and_original_assertion(case):
    module, assertion = load(case)
    assert (module.ENTRY, module.PHASE_END) == case[2:]
    subprocess.check_call(["git", "merge-base", "--is-ancestor", case[2], case[3]], cwd=ROOT)
    phase = "150L" if "150l" in case[0] else "150M"
    subjects = git(ROOT, "log", "--format=%s", case[2] + ".." + case[3]).splitlines()
    assert len(subjects) == (3 if phase == "150L" else 2)
    assert all(subject.startswith("Phase " + phase + ":") for subject in subjects)
    assertion()


def test_production_contract_and_historical_artifacts_remain_unchanged():
    # Once committed, freeze this maintenance phase too; later phases may evolve.
    commits = git(ROOT, "log", "--format=%H %s").splitlines()
    own = [line.split(" ", 1)[0] for line in commits if " Phase 150N:" in line]
    endpoint = own[0] if own else None
    protected = ["src/pcae", "docs/contracts", "docs/PHASE_150L_GENERATION_PROVENANCE_ARCHITECTURE.md",
                 "docs/PHASE_150M_HISTORICAL_FREEZE_ARCHITECTURE_REVALIDATION.md"]
    protected += git(ROOT, "ls-tree", "-r", "--name-only", ENTRY, "--", ".pcae/phase-reports",
                     ".pcae/finalization-transactions", ".pcae/delivery-receipts").splitlines()
    protected = [p for p in protected if not p.endswith("latest.json") and not p.endswith("latest.md")]
    revision_args = [ENTRY, endpoint] if endpoint else [ENTRY]
    assert git(ROOT, "diff", "--name-only", "--no-renames", *revision_args, "--", *protected) == ""
    contract = ROOT / "docs/contracts/LIFECYCLE_GENERATION_PROVENANCE_CONTRACT.md"
    assert hashlib.sha256(contract.read_bytes()).hexdigest() == "d72d93451a28befd39febd51473e05f020649afe26886742838a1adae119c51f"
