"""Phase 149O.20L.7O.2S.1 — FGSC-001 Structured Fast Green Self-Certification
Lifecycle Contract Independent Verification (fresh, not copied from 2S).

FGSC-001 (`docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md`)
is contract text only -- no implementation exists yet (2R's checkpoint-vs-
final-HEAD lifecycle machinery is not built; this contract only specifies
what a future implementation must do). These tests therefore verify the
*contract text itself* against two things: (1) its own internal structural
soundness, and (2) live, reproducible Git/production-source evidence --
never trusting 2S's or 2R.1's own prose as proof. No production source is
imported or exercised; every check here is either a text-structure check on
the frozen contract or a direct `git`/filesystem inspection of this
repository's real history.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md"

# The real, historical 2R commit range this contract's companion phase
# document (PHASE_149O_20L_7O_2S_...md, S3) reconstructs and builds its
# empirical Class A/B validation on. Independently re-confirmed by this
# phase via `git log --oneline 0773b21e..04d58ecf` before writing these
# tests -- exact match to both 2R.1 S1 and 2S S3's own reconstruction.
CHECKPOINT_COMMIT = "96ecd238"
FINAL_2R_HEAD = "04d58ecf"


def _norm(text: str) -> str:
    """Collapses whitespace/line-wrap so phrase-membership checks are not
    fragile to the contract's own Markdown line-wrapping."""
    return re.sub(r"\s+", " ", text)


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Contract identity / structure
# ---------------------------------------------------------------------------


def test_contract_identity_header(contract_text: str) -> None:
    assert "**Contract:** FGSC-001" in contract_text
    assert "**Version:** 1.0" in contract_text
    assert "**Status:** FROZEN" in contract_text


def test_section_numbering_is_sequential_no_gaps_no_duplicates(contract_text: str) -> None:
    numbers = [int(n) for n in re.findall(r"^## (\d+)\.", contract_text, re.MULTILINE)]
    assert numbers, "no numbered sections found"
    assert numbers == sorted(numbers), "sections are out of order"
    assert len(numbers) == len(set(numbers)), f"duplicate section numbers: {numbers}"
    assert numbers == list(range(numbers[0], numbers[-1] + 1)), (
        f"gap in section numbering: {numbers}"
    )
    # Section 0 (Normative language) through 23 (Amendment), per this
    # phase's own read of the frozen contract.
    assert numbers[0] == 0
    assert numbers[-1] == 23


def test_amendment_section_requires_explicit_version_increment(contract_text: str) -> None:
    amendment = contract_text.split("## 23. Amendment")[-1]
    assert "version increment" in amendment
    assert "v1.1" in amendment


# ---------------------------------------------------------------------------
# 2. Lifecycle state machine — mechanically parsed and modeled
# ---------------------------------------------------------------------------

_STATES = {
    "IMPLEMENTING",
    "CANDIDATE_FROZEN",
    "BEHAVIOR_VERIFIED",
    "FINALIZING",
    "FINALIZATION_VERIFIED",
    "READY_TO_PUSH",
    "PUSHED",
    "COMPLETE",
}


def _extract_state_machine_block(contract_text: str) -> str:
    match = re.search(r"```\n(IMPLEMENTING\n.*?)\n```", contract_text, re.DOTALL)
    assert match, "state machine fenced code block not found in contract S9"
    return match.group(1)


def _parse_transitions(block: str) -> set[tuple[str, str]]:
    """Parses `SRC\\n  -> DST  [...]` lines into (src, dst) edges. The block
    groups consecutive `-> DST` lines under a preceding bare state-name
    line, which is itself the source for all of them until the next bare
    state-name line. `[...]` annotations may wrap onto further, unindented-
    arrow continuation lines -- those are neither a new source header nor a
    new transition and must be skipped, not misread as either."""
    edges: set[tuple[str, str]] = set()
    current_src = None
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("->"):
            assert current_src is not None, f"transition with no source state: {line!r}"
            dst = line[2:].strip().split()[0]
            edges.add((current_src, dst))
        elif line in _STATES:
            current_src = line
        # else: a wrapped `[...]` annotation continuation line -- skip.
    return edges


def test_state_machine_has_exactly_eight_named_states(contract_text: str) -> None:
    block = _extract_state_machine_block(contract_text)
    mentioned = {tok for tok in re.findall(r"[A-Z_]{4,}", block) if tok in _STATES}
    assert mentioned == _STATES, (
        f"state machine block does not mention exactly the 8 expected states: "
        f"missing={_STATES - mentioned}, extra={mentioned - _STATES}"
    )


def test_state_machine_every_state_reachable_from_implementing(contract_text: str) -> None:
    block = _extract_state_machine_block(contract_text)
    edges = _parse_transitions(block)
    reachable = {"IMPLEMENTING"}
    frontier = {"IMPLEMENTING"}
    while frontier:
        nxt = {dst for (src, dst) in edges if src in frontier} - reachable
        reachable |= nxt
        frontier = nxt
    assert reachable == _STATES, f"unreachable states from IMPLEMENTING: {_STATES - reachable}"


def test_state_machine_complete_is_terminal(contract_text: str) -> None:
    block = _extract_state_machine_block(contract_text)
    edges = _parse_transitions(block)
    outgoing_from_complete = {dst for (src, dst) in edges if src == "COMPLETE"}
    assert outgoing_from_complete == set(), (
        f"COMPLETE has outgoing transitions, is not terminal: {outgoing_from_complete}"
    )


def test_state_machine_no_direct_edge_to_complete_except_from_pushed(contract_text: str) -> None:
    block = _extract_state_machine_block(contract_text)
    edges = _parse_transitions(block)
    sources_reaching_complete = {src for (src, dst) in edges if dst == "COMPLETE"}
    assert sources_reaching_complete == {"PUSHED"}, (
        "an unverified-behavior state has a direct edge to COMPLETE: "
        f"{sources_reaching_complete}"
    )


def test_state_machine_no_edge_skips_behavior_verification(contract_text: str) -> None:
    """IMPLEMENTING and CANDIDATE_FROZEN (states prior to a passed Stage A)
    must not have any edge directly into FINALIZING or later -- Stage A
    (BEHAVIOR_VERIFIED) must always be the gate."""
    block = _extract_state_machine_block(contract_text)
    edges = _parse_transitions(block)
    post_behavior_states = {
        "FINALIZING",
        "FINALIZATION_VERIFIED",
        "READY_TO_PUSH",
        "PUSHED",
        "COMPLETE",
    }
    for src in ("IMPLEMENTING", "CANDIDATE_FROZEN"):
        illegal = {dst for (s, dst) in edges if s == src and dst in post_behavior_states}
        assert not illegal, f"{src} has an edge that skips behavioral verification: {illegal}"


def test_state_machine_correction_loop_returns_to_finalizing_not_earlier(
    contract_text: str,
) -> None:
    """The push-state-correction loop (S12) must re-enter FINALIZING with
    the *same* checkpoint, never re-triggering Stage A by routing back to
    IMPLEMENTING or CANDIDATE_FROZEN."""
    block = _extract_state_machine_block(contract_text)
    edges = _parse_transitions(block)
    from_pushed = {dst for (src, dst) in edges if src == "PUSHED"}
    assert from_pushed == {"COMPLETE", "FINALIZING"}, (
        f"PUSHED has unexpected transition set: {from_pushed}"
    )


# ---------------------------------------------------------------------------
# 3. Post-checkpoint path classification — text-level checks
# ---------------------------------------------------------------------------


def test_class_a_forbids_production_test_and_contract_paths(contract_text: str) -> None:
    class_a_block = contract_text.split("**Class A")[1].split("**Class B")[0]
    for token in ("src/pcae/**", "scripts/**", "tests/**", "docs/contracts/**"):
        assert token in class_a_block, f"{token!r} missing from Class A (forbidden) list"


def test_class_b_does_not_list_production_or_test_paths(contract_text: str) -> None:
    class_b_block = contract_text.split("**Class B")[1].split("**Content-sensitive")[0]
    for forbidden_token in ("src/pcae/", "scripts/", "tests/"):
        assert forbidden_token not in class_b_block, (
            f"Class B (permitted) list unexpectedly contains {forbidden_token!r}"
        )


def test_unknown_path_defaults_to_forbidden_fail_closed(contract_text: str) -> None:
    assert "Unknown defaults to class C (forbidden)" in contract_text
    assert "fail closed" in contract_text.split("## 4.")[1].split("## 5.")[0]


def test_diff_authority_rejects_commit_message_as_evidence(contract_text: str) -> None:
    section_6 = contract_text.split("## 6.")[1].split("## 7.")[0]
    assert "Commit message text is explicitly" in section_6
    assert "not** authority" in section_6


def test_merge_commits_unconditionally_rejected(contract_text: str) -> None:
    section_7 = _norm(contract_text.split("## 7.")[1].split("## 8.")[0])
    assert "rejected outright" in section_7
    assert "No exception is authorized by this contract" in section_7


def test_history_rewrite_unconditionally_invalidates_checkpoint(contract_text: str) -> None:
    section_7 = _norm(contract_text.split("## 7.")[1].split("## 8.")[0])
    assert "invalidates the checkpoint unconditionally" in section_7
    assert "No substitute checkpoint may be chosen after the fact" in section_7


# ---------------------------------------------------------------------------
# 4. Five-condition freshness replacement — completeness
# ---------------------------------------------------------------------------


def test_freshness_replacement_has_exactly_five_conditions(contract_text: str) -> None:
    section_14 = contract_text.split("## 14.")[1].split("## 15.")[0]
    condition_numbers = re.findall(r"^\d+\. `?", section_14, re.MULTILINE)
    assert len(condition_numbers) == 5, (
        f"expected exactly 5 freshness conditions, found {len(condition_numbers)}"
    )


def test_freshness_condition_one_is_unweakened_candidate_equality(contract_text: str) -> None:
    section_14 = contract_text.split("## 14.")[1].split("## 15.")[0]
    assert "candidate_commit == verification_checkpoint_commit" in section_14
    assert "Condition 1 is **exactly** today's check, unweakened" in section_14


# ---------------------------------------------------------------------------
# 5. Scope limits / non-goals — the contract must not overreach
# ---------------------------------------------------------------------------


def test_contract_explicitly_disclaims_implementation(contract_text: str) -> None:
    header = _norm(contract_text.split("## 0.")[0])
    assert "no implementation is authorized or performed by this contract's freezing" in header


def test_contract_does_not_touch_fast_green_arithmetic_or_scalar_path(contract_text: str) -> None:
    header = _norm(contract_text.split("## 0.")[0])
    assert "does not modify" in header
    assert "_fast_green_failure_signal()" in header
    assert "the scalar `fast_green` path" in header
    assert "validate_structured_fast_green()`'s existing arithmetic" in header


def test_contract_does_not_reconcile_phase_2p(contract_text: str) -> None:
    header = _norm(contract_text.split("## 0.")[0])
    assert "does not reconcile, promote, or reclassify Phase 149O.20L.7O.2P" in header
    section_20 = _norm(contract_text.split("## 20.")[1].split("## 21.")[0])
    assert "Phase 149O.20L.7O.2P reconciliation" in section_20


def test_scalar_mode_backward_compatibility_frozen(contract_text: str) -> None:
    section_16 = _norm(contract_text.split("## 16.")[1].split("## 17.")[0])
    assert "This contract introduces no forced migration" in section_16


def test_self_hosting_acceptance_tests_not_executed_by_this_freeze(contract_text: str) -> None:
    section_22 = contract_text.split("## 22.")[1].split("## 23.")[0]
    assert "Neither test is executed by this contract-freezing phase" in section_22
    assert "22.1" in section_22 and "22.2" in section_22


# ---------------------------------------------------------------------------
# 6. Live-history empirical validation — the contract's central claim,
#    re-derived directly from real Git history, never trusted from prose.
# ---------------------------------------------------------------------------


def test_checkpoint_and_final_head_shas_are_real_ancestors(contract_text: str) -> None:
    """`verification_checkpoint_commit` must be a real ancestor of
    `final_phase_head` for the exact historical case this contract's
    companion phase document reconstructs (2R's own self-certification
    attempt)."""
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", CHECKPOINT_COMMIT, FINAL_2R_HEAD],
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, (
        f"{CHECKPOINT_COMMIT} is not an ancestor of {FINAL_2R_HEAD} in live repo history"
    )


def test_post_checkpoint_delta_is_entirely_class_b_by_live_diff(contract_text: str) -> None:
    """Mechanically re-derives the contract's own central empirical claim
    (S3 of the companion phase doc): every path touched in the real
    checkpoint..final-HEAD range for 2R's historical self-certification
    attempt falls inside the Class B allowlist -- never trusting the
    companion doc's table, re-computed fresh here from `git diff`."""
    changed = _git(
        "diff", "--name-only", f"{CHECKPOINT_COMMIT}..{FINAL_2R_HEAD}"
    ).splitlines()
    assert changed, "expected a non-empty historical post-checkpoint delta"

    allowed_prefixes = (
        ".pcae/phase-completion-metadata.json",
        ".pcae/phase-completion-report.md",
        ".pcae/fast-green-attribution/",
        "PROJECT_STATUS.md",
        "CHANGELOG.md",
        "tasks/DONE.md",
        "tasks/active/",
        "tasks/done/",
    )
    forbidden_prefixes = ("src/pcae/", "scripts/", "tests/", "docs/contracts/")

    for path in changed:
        assert not path.startswith(forbidden_prefixes), (
            f"post-checkpoint delta touches a Class-A (forbidden) path: {path}"
        )
        assert path.startswith(allowed_prefixes), (
            f"post-checkpoint delta touches a path outside the claimed Class B allowlist: {path}"
        )


def test_post_checkpoint_delta_contains_no_merge_commits(contract_text: str) -> None:
    """Mechanically confirms S7's merge-rejection rule would not have
    fired against 2R's own real history -- every intervening commit is
    single-parent, matching the contract's own empirical claim."""
    parents_output = _git(
        "log", f"{CHECKPOINT_COMMIT}..{FINAL_2R_HEAD}", "--format=%P"
    )
    for line in parents_output.splitlines():
        parent_count = len(line.split())
        assert parent_count == 1, (
            f"a merge commit (parents={parent_count}) exists in the historical "
            "checkpoint..final-HEAD range, contradicting the contract's own "
            "empirical single-parent claim"
        )


def test_freshness_check_line_citation_matches_live_source(contract_text: str) -> None:
    """S1 originally cited `src/pcae/core/fast_green_attribution.py:586-589`
    for the exact-equality freshness check. 149O.20L.7O.2S.4 relocated that
    check to run *last* in ``validate_structured_fast_green()`` (repair of
    the 2S.3 Blocking staleness-carve-out/attribution-completeness finding)
    -- it now lives at lines 789-796. Confirms the check still exists,
    unweakened, in the live source at its current location, rather than
    trusting either citation."""
    source_path = REPO_ROOT / "src" / "pcae" / "core" / "fast_green_attribution.py"
    lines = source_path.read_text(encoding="utf-8").splitlines()
    cited_block = "\n".join(lines[788:796])  # 0-indexed, lines 789-796
    assert "candidate_commit" in cited_block
    assert "actual_head" in cited_block
    assert "stale" in cited_block


def test_push_py_touches_no_fast_green_field(contract_text: str) -> None:
    """S17 claims `push.py` does not add structured-evidence interpretation
    and trusts only `compute_final_trust()`. Confirmed directly against
    live source."""
    source_path = REPO_ROOT / "src" / "pcae" / "commands" / "push.py"
    text = source_path.read_text(encoding="utf-8")
    assert "compute_final_trust" in text
    assert "fast_green_attribution" not in text
    assert "validate_structured_fast_green" not in text


def test_phase_report_consistency_is_reachable_only_via_cli_dispatch(contract_text: str) -> None:
    """S19 claims `pcae phase-report consistency` gates nothing and is a
    standalone diagnostic. Confirmed: its handler function is referenced
    nowhere in src/pcae outside the CLI argparse wiring itself."""
    hits = _git(
        "grep", "-n", "-r", "run_phase_report_consistency", "--", "src/pcae"
    )
    call_sites = [
        line for line in hits.splitlines() if "def run_phase_report_consistency" not in line
    ]
    non_cli_call_sites = [line for line in call_sites if "cli.py" not in line]
    assert not non_cli_call_sites, (
        f"run_phase_report_consistency is referenced outside CLI dispatch, "
        f"may be gating another command: {non_cli_call_sites}"
    )


def test_fgsc_001_contract_file_is_not_in_hmic_frozen_digest_set() -> None:
    """S4 of the contract cites `docs/contracts/**` as 'content-digest-bound
    by existing tests' to justify Class A. Confirms directly against the
    live HMIC frozen-file enumeration that this is true only for a fixed,
    narrow 7-file subset of docs/contracts/*.md (the HATP/HMIC contracts) --
    not for `docs/contracts/**` as a category, and not for FGSC-001's own
    contract file, which is absent from that enumeration. This does not
    make Class A's classification of docs/contracts/** *wrong* (it remains
    the conservative, safe choice on independent content-sensitivity
    grounds per S4's own separate content-class rule) -- it demonstrates
    the *evidentiary justification offered in the contract's own prose* is
    broader than what the cited test actually establishes."""
    hmic_source = (
        REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
    ).read_text(encoding="utf-8")
    assert "FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md" not in hmic_source
    docs_contracts_entries = set(re.findall(r'"docs/contracts/[^"]+\.md"', hmic_source))
    assert len(docs_contracts_entries) == 7, (
        "expected a small, fixed 7-file enumeration of docs/contracts/*.md "
        f"files in the HMIC frozen set, found {len(docs_contracts_entries)}: "
        f"{sorted(docs_contracts_entries)}"
    )
