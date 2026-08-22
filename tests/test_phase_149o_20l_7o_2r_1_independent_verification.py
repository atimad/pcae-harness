"""Phase 149O.20L.7O.2R.1 — Independent Verification (fresh, not copied from 2R).

Adversarial unit-level attacks against `pcae.core.fast_green_attribution`'s
`validate_structured_fast_green`, the trust boundary enforced at phase
completion time. Deliberately does not import or reuse anything from
`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`.
"""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from pcae.core import fast_green_attribution as fga


def _run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()


def _init_repo(tmp_path: Path, phase_id: str = "TESTPHASE1") -> tuple[Path, str, str]:
    """Two-commit repo: commit0 (baseline) then a 'Phase <id>: ...' commit
    (HEAD == candidate). Returns (repo_path, baseline_sha, candidate_sha)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q"], repo)
    _run(["git", "config", "user.email", "t@t.example"], repo)
    _run(["git", "config", "user.name", "Tester"], repo)
    (repo / "f.txt").write_text("0")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", "initial commit"], repo)
    baseline_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    (repo / "f.txt").write_text("1")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", f"Phase {phase_id}: start work"], repo)
    candidate_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()
    return repo, baseline_sha, candidate_sha


def _advance(repo: Path) -> str:
    (repo / "f.txt").write_text("2")
    _run(["git", "add", "."], repo)
    _run(["git", "commit", "-q", "-m", "unrelated follow-up commit"], repo)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True
    ).stdout.strip()


def _base_evidence(baseline: str, candidate: str, *, raw_failed=None, raw_errors=None,
                    baseline_raw_failed=None, baseline_raw_errors=None,
                    attributable_failures=None, excluded_preexisting_failures=None,
                    excluded_environment_failures=None, expected_phase_artifacts=None) -> dict:
    return {
        "schema_version": fga.SCHEMA_VERSION,
        "method": "baseline_vs_candidate_isolated_worktree",
        "baseline_commit": baseline,
        "baseline_method": "parent_of_oldest_phase_attributed_commit",
        "candidate_commit": candidate,
        "command": " ".join(["python3", "-m", "pytest", *fga.FAST_GREEN_PYTEST_ARGS]).replace(
            "python3", __import__("sys").executable
        ),
        "generated_at": "2026-08-22T00:00:00+00:00",
        "baseline_raw_failed": sorted(baseline_raw_failed or []),
        "baseline_raw_errors": sorted(baseline_raw_errors or []),
        "raw_failed": sorted(raw_failed or []),
        "raw_errors": sorted(raw_errors or []),
        "attributable_failures": sorted(attributable_failures or []),
        "excluded_preexisting_failures": excluded_preexisting_failures or [],
        "excluded_environment_failures": excluded_environment_failures or [],
        "expected_phase_artifacts": expected_phase_artifacts or [],
    }


def _persist(repo_root: Path, evidence: dict) -> dict:
    return fga.persist_evidence(str(repo_root), evidence)


def _load_artifact(repo_root: Path, structured_value: dict) -> dict:
    artifact_abs = repo_root / structured_value["provenance"]["artifact_path"]
    with open(artifact_abs) as fh:
        return json.load(fh)


def _write_artifact(repo_root: Path, structured_value: dict, content: dict) -> None:
    artifact_abs = repo_root / structured_value["provenance"]["artifact_path"]
    with open(artifact_abs, "w") as fh:
        json.dump(content, fh, sort_keys=True, indent=2)
        fh.write("\n")


def _retamper(repo_root: Path, structured_value: dict, mutate) -> dict:
    """Realistic attacker flow: edit the persisted artifact file AND update
    the embedded/inline report value to match, recomputing a self-consistent
    digest — exactly the threat model the phase brief specifies."""
    persisted = _load_artifact(repo_root, structured_value)
    mutate(persisted)
    _write_artifact(repo_root, structured_value, persisted)
    new_digest = fga._canonical_digest(persisted)
    new_value = dict(persisted)
    new_value["provenance"] = dict(structured_value["provenance"])
    new_value["provenance"]["artifact_digest"] = new_digest
    return new_value


# ---------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------

def test_01_valid_artifact_raw_nonzero_zero_attributable_is_accepted(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        baseline_raw_failed=["tests/test_x.py::test_a"],
        excluded_preexisting_failures=[{
            "node_id": "tests/test_x.py::test_a",
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues == [], issues


# ---------------------------------------------------------------------
# 2. Move an attributable node into claimed-preexisting (labels-only lie)
# ---------------------------------------------------------------------

def test_02_relabel_attributable_as_preexisting_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    # test_b is a genuinely NEW candidate-only failure (not in baseline).
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_b"],
        baseline_raw_failed=[],
        attributable_failures=["tests/test_x.py::test_b"],
    )
    value = _persist(repo, evidence)
    tampered = _retamper(repo, value, lambda p: (
        p.__setitem__("attributable_failures", []),
        p.__setitem__("excluded_preexisting_failures", [{
            "node_id": "tests/test_x.py::test_b",
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }]),
    ))
    issues = fga.validate_structured_fast_green(
        tampered, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues, "relabeling a genuine attributable failure as preexisting must be rejected"
    assert any("excluded_preexisting_failures" in i for i in issues)


# ---------------------------------------------------------------------
# 3a. Delete a baseline entry -> forces a genuinely-preexisting node to
#     become attributable. Self-defeating for an attacker either way.
# ---------------------------------------------------------------------

def test_03a_deleting_baseline_entry_cannot_produce_false_accept(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        baseline_raw_failed=["tests/test_x.py::test_a"],
        excluded_preexisting_failures=[{
            "node_id": "tests/test_x.py::test_a",
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }],
    )
    value = _persist(repo, evidence)
    # Attacker deletes the baseline entry but does NOT also update the
    # preexisting-claim bucket -> straightforward bucket mismatch.
    tampered = _retamper(repo, value, lambda p: p.__setitem__("baseline_raw_failed", []))
    issues = fga.validate_structured_fast_green(
        tampered, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues, "shrinking baseline set without correspondingly updating claims must be rejected"


def test_03a2_deleting_baseline_entry_and_updating_claims_reclassifies_as_attributable(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        baseline_raw_failed=["tests/test_x.py::test_a"],
        excluded_preexisting_failures=[{
            "node_id": "tests/test_x.py::test_a",
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }],
    )
    value = _persist(repo, evidence)
    # Attacker deletes baseline entry AND updates claims consistently ->
    # the node now has nowhere to go except attributable_failures, which
    # the final "nonzero attributable" check rejects outright. Confirms
    # there is no route to a false PASS via baseline-shrinking.
    tampered = _retamper(repo, value, lambda p: (
        p.__setitem__("baseline_raw_failed", []),
        p.__setitem__("excluded_preexisting_failures", []),
        p.__setitem__("attributable_failures", ["tests/test_x.py::test_a"]),
    ))
    issues = fga.validate_structured_fast_green(
        tampered, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues, "a real attributable failure must still block completion"
    assert any("nonzero attributable_failures" in i for i in issues)


# ---------------------------------------------------------------------
# 3b. THE CENTRAL FINDING: forge a baseline entry to launder a genuine
#     candidate-only (attributable) failure into "preexisting".
# ---------------------------------------------------------------------

def test_03b_forging_a_baseline_entry_launders_a_real_regression_FINDING(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    # test_b genuinely fails ONLY on the candidate; baseline never ran it
    # failing. This is a real, attributable regression.
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_b"],
        baseline_raw_failed=[],
        attributable_failures=["tests/test_x.py::test_b"],
    )
    value = _persist(repo, evidence)

    # FINDING: validate_structured_fast_green never independently re-runs
    # pytest against baseline_commit to verify baseline_raw_failed/
    # baseline_raw_errors are truthful. It only (a) checks baseline_commit
    # itself equals derive_phase_entry_baseline()'s derivation, and
    # (b) recomputes preexisting/attributable arithmetic FROM the
    # artifact's own self-reported baseline_raw_failed/baseline_raw_errors
    # lists. Those two lists are therefore trusted verbatim as ground
    # truth of "what actually failed at the baseline commit" with no
    # independent execution or cross-check. An attacker (or a caller who
    # runs `pcae phase fast-green-attribution` against a baseline whose
    # true raw-failure set was never captured/verified elsewhere) who
    # forges an extra baseline_raw_failed entry equal to a genuine
    # candidate-only failure — and updates excluded_preexisting_failures
    # and attributable_failures consistently, then recomputes a fully
    # self-consistent digest — produces an artifact that passes every
    # check in validate_structured_fast_green with ZERO issues, laundering
    # a real regression into "pre-existing". This is the load-bearing gap:
    # "independently recomputes ... from raw node-ID sets" (module
    # docstring) is true only of the ARITHMETIC over those sets; the sets
    # themselves (specifically baseline_raw_failed/baseline_raw_errors)
    # are never independently re-derived by the validator itself — only
    # `build_attribution_evidence()`'s own real worktree run produces them
    # honestly when the CLI is used end-to-end. The validator alone cannot
    # distinguish an honest CLI-produced artifact from a hand-forged one
    # with self-consistent counts, beyond requiring baseline_commit to be
    # the correct SHA (it does not require baseline_raw_failed/errors to
    # be the correct CONTENT for that SHA).
    tampered = _retamper(repo, value, lambda p: (
        p.__setitem__("baseline_raw_failed", ["tests/test_x.py::test_b"]),
        p.__setitem__("attributable_failures", []),
        p.__setitem__("excluded_preexisting_failures", [{
            "node_id": "tests/test_x.py::test_b",
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }]),
    ))
    issues = fga.validate_structured_fast_green(
        tampered, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    # Documents ACTUAL current behavior: this forged, internally-consistent
    # artifact is ACCEPTED (issues == []) despite laundering a real
    # attributable regression as pre-existing.
    assert issues == [], (
        "if this assertion ever fails because issues is non-empty, the gap "
        f"described above has been closed by some other mechanism; got: {issues}"
    )


# ---------------------------------------------------------------------
# 4. Digest mismatch (content tampered, digest NOT updated)
# ---------------------------------------------------------------------

def test_04_digest_mismatch_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    persisted = _load_artifact(repo, value)
    persisted["method"] = "tampered_method_string"
    _write_artifact(repo, value, persisted)  # digest in `value` now stale
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("digest mismatch" in i for i in issues)


# ---------------------------------------------------------------------
# 5. artifact_path escapes repo root
# ---------------------------------------------------------------------

@pytest.mark.parametrize("bad_path", ["../../etc/passwd", "/etc/passwd"])
def test_05_artifact_path_escape_is_rejected(tmp_path, bad_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    value = dict(value)
    value["provenance"] = dict(value["provenance"])
    value["provenance"]["artifact_path"] = bad_path
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("escapes repository root" in i for i in issues)


# ---------------------------------------------------------------------
# 6. Hallucinated artifact_path pointing to a nonexistent file
# ---------------------------------------------------------------------

def test_06_nonexistent_artifact_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    value = dict(value)
    value["provenance"] = dict(value["provenance"])
    value["provenance"]["artifact_path"] = ".pcae/fast-green-attribution/deadbeef.json"
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("artifact not found" in i for i in issues)


# ---------------------------------------------------------------------
# 7. Stale candidate_commit
# ---------------------------------------------------------------------

def test_07_stale_candidate_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    _advance(repo)  # HEAD moves past `candidate`
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("stale" in i for i in issues)


# ---------------------------------------------------------------------
# 8. Wrong / arbitrary baseline_commit
# ---------------------------------------------------------------------

def test_08_arbitrary_baseline_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    # Use candidate's own SHA as a bogus "baseline" (an obviously wrong,
    # attacker-convenient choice — collapses the whole diff to zero).
    evidence = _base_evidence(candidate, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("baseline is not authoritative" in i for i in issues)


# ---------------------------------------------------------------------
# 9. Duplicate node ID across raw_failed and raw_errors
# ---------------------------------------------------------------------

def test_09_duplicate_node_across_failed_and_errors_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        raw_errors=["tests/test_x.py::test_a"],
        baseline_raw_failed=[],
        attributable_failures=["tests/test_x.py::test_a"],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("overlap" in i for i in issues)


# ---------------------------------------------------------------------
# 10. Omitted raw node (claimed buckets don't cover a real raw failure)
# ---------------------------------------------------------------------

def test_10_omitted_raw_node_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a", "tests/test_x.py::test_b"],
        baseline_raw_failed=[],
        attributable_failures=["tests/test_x.py::test_a"],  # test_b silently dropped
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("attributable_failures does not match" in i for i in issues)


# ---------------------------------------------------------------------
# 11. Malformed environment-exclusion entry
# ---------------------------------------------------------------------

def test_11_malformed_environment_entry_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        baseline_raw_failed=[],
        excluded_environment_failures=[{
            "node_id": "tests/test_x.py::test_a",
            "rerun_result": "flaky",  # not in {"pass","divergent_error"}
            "rerun_at": "2026-08-22T00:00:00+00:00",
            "rerun_commit": candidate,
        }],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("lacks required machine-evidence fields" in i for i in issues)


# ---------------------------------------------------------------------
# 12. Environment exclusions exceed the bounded policy
# ---------------------------------------------------------------------

def test_12_environment_exclusion_bound_exceeded_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    nodes = [f"tests/test_x.py::test_{i}" for i in range(4)]
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=nodes,
        baseline_raw_failed=[],
        excluded_environment_failures=[{
            "node_id": n, "rerun_result": "pass",
            "rerun_at": "2026-08-22T00:00:00+00:00", "rerun_commit": candidate,
        } for n in nodes],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("exceeds the bounded policy" in i for i in issues)


# ---------------------------------------------------------------------
# 13. Wrong test name claimed as expected_phase_artifacts
# ---------------------------------------------------------------------

def test_13_wrong_expected_artifact_test_name_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    node = "tests/test_x.py::test_unrelated_thing"
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=[node],
        baseline_raw_failed=[],
        expected_phase_artifacts=[{
            "node_id": node, "predicted_by": "pushed_status", "predicted_value": "local_only",
        }],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("does not match the closed test identity" in i for i in issues)


# ---------------------------------------------------------------------
# 14. expected_phase_artifacts claimed while pushed_status is a pushed literal
# ---------------------------------------------------------------------

@pytest.mark.parametrize("pushed_literal", ["pushed", "clean", "nothing_to_push"])
def test_14_expected_artifact_while_already_pushed_is_rejected(tmp_path, pushed_literal):
    repo, baseline, candidate = _init_repo(tmp_path)
    node = "tests/test_push.py::test_head_equals_origin_main"
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=[node],
        baseline_raw_failed=[],
        expected_phase_artifacts=[{
            "node_id": node, "predicted_by": "pushed_status", "predicted_value": pushed_literal,
        }],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status=pushed_literal,
    )
    assert issues
    assert any("already a pushed literal" in i for i in issues)


# ---------------------------------------------------------------------
# 15. predicted_value mismatch vs the validator's actual pushed_status input
# ---------------------------------------------------------------------

def test_15_expected_artifact_predicted_value_mismatch_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    node = "tests/test_push.py::test_head_equals_origin_main"
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=[node],
        baseline_raw_failed=[],
        expected_phase_artifacts=[{
            "node_id": node, "predicted_by": "pushed_status", "predicted_value": "local_only",
        }],
    )
    value = _persist(repo, evidence)
    # Validator is called with a DIFFERENT actual pushed_status than the
    # artifact predicted -> pushed_status is validator-input-authoritative,
    # not trusted from the artifact itself.
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="stale_local_only",
    )
    assert issues
    assert any("predicted_value" in i for i in issues)
    # NOTE: this test only proves the validator function itself treats its
    # `pushed_status` PARAMETER as authoritative over the artifact's claim.
    # It does NOT establish where phase_reports.validate_derived_correctness
    # sources the `pushed_status` value it passes in (report.pushed_status)
    # or whether THAT field is itself independently derived vs.
    # caller-declared — out of scope for this unit-level file; see the
    # coordinator's separate trace of report.pushed_status / push.py.


# ---------------------------------------------------------------------
# 16. Missing required top-level key
# ---------------------------------------------------------------------

def test_16_missing_provenance_key_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    del value["provenance"]
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("missing required key 'provenance'" in i for i in issues)


# ---------------------------------------------------------------------
# 17. Scalar-shaped dict is NOT routed to the structured path
# ---------------------------------------------------------------------

def test_17_scalar_shaped_dict_is_not_structured():
    assert fga.is_structured_fast_green({"failed": 0}) is False
    assert fga.is_structured_fast_green({"passed": 4390, "failed": 0}) is False
    assert fga.is_structured_fast_green("0 passed, 0 failed") is False
    assert fga.is_structured_fast_green(None) is False


# ---------------------------------------------------------------------
# 18. Hybrid payload: correct schema_version + extra legacy keys
# ---------------------------------------------------------------------

def test_18_hybrid_payload_routes_to_structured_path_but_extra_keys_are_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(baseline, candidate, raw_failed=[], baseline_raw_failed=[])
    value = _persist(repo, evidence)
    hybrid = dict(value)
    hybrid["failed"] = 0  # legacy scalar-shaped key injected alongside
    hybrid["passed"] = 4390
    # Correctly routed to the structured path purely by schema_version...
    assert fga.is_structured_fast_green(hybrid) is True
    # ...but is actually STRICTER than assumed: validate_structured_fast_green
    # compares every non-"provenance" inline key against the persisted
    # artifact's content (`persisted.get(key) != value.get(key)`), and the
    # persisted artifact has no "failed"/"passed" keys at all, so
    # `persisted.get(key)` is None for both -> mismatch -> rejected. There
    # is no ambiguous-interpretation hybrid acceptance path: any inline key
    # not present verbatim in the persisted artifact is rejected outright,
    # legacy-shaped or not. No gap found here.
    issues = fga.validate_structured_fast_green(
        hybrid, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("field 'failed' diverges" in i for i in issues)
    assert any("field 'passed' diverges" in i for i in issues)


# ---------------------------------------------------------------------
# 19. Cross-bucket overlap: genuinely preexisting node also claimed as
#     an environment exclusion
# ---------------------------------------------------------------------

def test_19_preexisting_environment_overlap_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    node = "tests/test_x.py::test_a"
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=[node],
        baseline_raw_failed=[node],
        excluded_preexisting_failures=[{
            "node_id": node, "baseline_commit": baseline, "baseline_evidence": "failed_in_baseline",
        }],
        # Same node ALSO fabricated as an environment exclusion.
        excluded_environment_failures=[{
            "node_id": node, "rerun_result": "pass",
            "rerun_at": "2026-08-22T00:00:00+00:00", "rerun_commit": candidate,
        }],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("bucket membership overlaps" in i for i in issues)


# ---------------------------------------------------------------------
# 20. Empty-string node_id in excluded_preexisting_failures
# ---------------------------------------------------------------------

def test_20_empty_node_id_in_preexisting_entry_is_rejected(tmp_path):
    repo, baseline, candidate = _init_repo(tmp_path)
    evidence = _base_evidence(
        baseline, candidate,
        raw_failed=["tests/test_x.py::test_a"],
        baseline_raw_failed=["tests/test_x.py::test_a"],
        excluded_preexisting_failures=[{
            "node_id": "",  # empty/falsy node_id
            "baseline_commit": baseline,
            "baseline_evidence": "failed_in_baseline",
        }],
        attributable_failures=["tests/test_x.py::test_a"],
    )
    value = _persist(repo, evidence)
    issues = fga.validate_structured_fast_green(
        value, repo_root=str(repo), phase_id="TESTPHASE1", pushed_status="local_only",
    )
    assert issues
    assert any("malformed excluded_preexisting_failures entry" in i for i in issues)
