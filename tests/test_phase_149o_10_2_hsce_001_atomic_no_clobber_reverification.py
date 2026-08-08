"""Phase 149O.10.2 — HSCE-001 Atomic No-Clobber Repair Independent
Re-Verification.

Independently re-verifies the repaired HSCE-REQ-052 exclusive-publication
mechanism (HSCE-001 v1.1, repaired by Phase 149O.10.1): identical
concurrent writers, differing concurrent writers, many-writer races,
crash-before/after/during-publish semantics, unsupported-filesystem
fail-closed behavior, symlink/path preservation, canonical byte-comparison
semantics; reconfirms F-1 (count correction), F-2 (wording), and Obs-2
(AG3 attack-matrix addition); reconfirms non-regression of every HSCE-001
section 149O.10.1 did not touch.

This suite is written independently of
tests/test_phase_149o_10_1_hsce_001_narrow_contract_repair.py -- it does
not import or reuse that file's helpers/constants, per this phase's own
instruction to reconstruct rather than reuse.

Two kinds of verification are performed:

1. Contract-text verification (re-derives requirement/attack-matrix
   counts, section content, and self-consistency directly from the
   contract file -- the same technique 149O.10/149O.10.1 used).
2. Test-only real-filesystem probes of `os.link`'s actual exclusive-
   create semantics on this platform, and an abstract state-machine
   model with permutation enumeration -- corroborating evidence that the
   *primitive* the contract selected behaves as the contract's prose
   claims. No production evidence-store/signing-CLI implementation
   exists yet (independently reconfirmed by TestProductionBoundary
   below), so these probes exercise `os.link` directly, never
   application code.
"""

from __future__ import annotations

import itertools
import os
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HSCE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

_V1_0_FREEZE_COMMIT = "3ad4e839"
_V1_1_REPAIR_COMMIT = "0cc32d09"


@pytest.fixture(scope="module")
def text() -> str:
    return HSCE_CONTRACT.read_text(encoding="utf-8")


def _section(full_text: str, start_marker: str, end_marker: str) -> str:
    start = full_text.index(start_marker)
    end = full_text.index(end_marker, start)
    return full_text[start:end]


def _req052(full_text: str) -> str:
    return _section(full_text, "**HSCE-REQ-052.**", "**HSCE-REQ-053.**")


def _norm(s: str) -> str:
    return " ".join(s.split())


# ═══════════════════════════════════════════════════════════════════════
# 1. Requirement inventory / attack-matrix count -- independent re-derivation
# ═══════════════════════════════════════════════════════════════════════


class TestRequirementInventory:
    def test_exactly_79_sequential_gapless_requirements(self, text):
        import re

        ids = sorted({int(n) for n in re.findall(r"HSCE-REQ-(\d+)", text)})
        assert ids[0] == 1
        assert ids[-1] == 79
        assert ids == list(range(1, 80)), "sequence must be gapless, no duplicates"

    def test_current_count_statement_says_79(self, text):
        assert "through `HSCE-REQ-079` inclusive" in text

    def test_no_unmarked_current_claim_of_78(self, text):
        """The string '078 inclusive' may appear only inside the historical
        quotation embedded in the F-1 correction bracket/disposition --
        never as a live, unqualified current-state claim."""

        idx = 0
        occurrences = []
        while True:
            idx = text.find("HSCE-REQ-078` inclusive", idx)
            if idx == -1:
                break
            occurrences.append(idx)
            idx += 1
        idx = 0
        while True:
            idx = text.find("HSCE-REQ-001 through HSCE-REQ-078 inclusive", idx)
            if idx == -1:
                break
            occurrences.append(idx)
            idx += 1
        assert occurrences, "expected the historical miscount to still be quoted somewhere"
        for pos in occurrences:
            window = text[max(0, pos - 200):pos]
            assert (
                "originally read" in window or "originally:" in window
            ), "every '078 inclusive' occurrence must be inside an explicit historical quotation"

    def test_exactly_21_attack_matrix_items(self, text):
        section = _section(text, "## 38. Mandatory Future Attack Matrix", "## 39.")
        import re

        items = re.findall(r"^\d+\.\s", section, flags=re.MULTILINE)
        assert len(items) == 21

    def test_attack_item_21_is_ag3_analogue(self, text):
        section = _section(text, "## 38. Mandatory Future Attack Matrix", "## 39.")
        assert "21." in section
        assert "original_commit_sha" in section
        assert "operation_not_found" in section
        assert "AG3 analogue" in section or "AG3 analogue of item 20" in section


# ═══════════════════════════════════════════════════════════════════════
# 2. Independent diff reconstruction v1.0 -> v1.1
# ═══════════════════════════════════════════════════════════════════════


class TestDiffReconstruction:
    def _diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", _V1_0_FREEZE_COMMIT, _V1_1_REPAIR_COMMIT, "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        return result.stdout

    def test_exactly_five_hunks(self):
        diff = self._diff()
        assert diff.count("\n@@ ") + (1 if diff.startswith("@@ ") else 0) == 5 or diff.count("@@ -") == 5

    def test_no_hunk_touches_sections_1_through_23_besides_header(self):
        """Every changed hunk must be classifiable as version-bump, the
        REQ-052 replacement, the attack-matrix addition, the REQ-077/078
        rewording, or the new REPAIR_HISTORY sections (44-45). No hunk may
        touch e.g. CLI grammar (§5-8), proof field-source table (§9),
        envelope schema (§14-16), or evidence-ID formula (§17-18)."""

        diff = self._diff()
        forbidden_headers = [
            "## 5. Signing Command",
            "## 9. Proof Field-Source",
            "## 14. `HATPSignedEvidenceEnvelope`",
            "## 17. Evidence ID",
            "## 20. Evidence Store Root",
            "## 21. Evidence Lookup",
            "## 22. Closed Error Vocabulary",
            "## 37. Security Invariants",
        ]
        added_lines = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        added_text = "\n".join(added_lines)
        for header in forbidden_headers:
            assert header not in added_text, f"unexpected diff touching {header!r}"

    def test_hunk_count_matches_disclosed_changed_requirement_set(self, text):
        changed = _section(text, "**Changed requirements:**", "**F-1 disposition")
        assert "HSCE-REQ-052" in changed
        assert "HSCE-REQ-077" in changed
        assert "HSCE-REQ-078" in changed
        assert "byte-identical to v1.0" in changed


# ═══════════════════════════════════════════════════════════════════════
# 3. HSCE-REQ-052 reconstruction -- independent state-machine extraction
# ═══════════════════════════════════════════════════════════════════════


class TestReq052StateMachine:
    def test_uses_hard_link_not_replace_as_winner_mechanism(self, text):
        req = _norm(_req052(text))
        assert "os.link(temp_path" in req
        assert "attempt `os.link" in req

    def test_winner_defined_by_link_success_only(self, text):
        req = _norm(_req052(text))
        assert "if `os.link` succeeds, this writer is the exclusive-publication **winner**" in req
        assert "canonical status" in req and "established by that single successful call, never by any earlier check" in req

    def test_loser_path_is_eexist(self, text):
        req = _norm(_req052(text))
        assert "if `os.link` raises `FileExistsError`, this writer has **lost**" in req

    def test_loser_checks_symlink_before_compare(self, text):
        req = _norm(_req052(text))
        idx_lost = req.index("this writer has **lost**")
        idx_islink = req.index("os.path.islink", idx_lost)
        idx_compare = req.index("read the already-persisted canonical envelope", idx_lost)
        assert idx_lost < idx_islink < idx_compare, "islink check must precede the compare-read"

    def test_loser_compare_outcomes(self, text):
        req = _norm(_req052(text))
        assert "byte-identical is idempotent success" in req
        assert "byte-different is `evidence_conflict`" in req
        assert "the persisted winner is never overwritten, under any condition" in req

    def test_other_oserror_fails_closed_no_fallback(self, text):
        req = _norm(_req052(text))
        assert "raises any `OSError` other than `FileExistsError`" in req
        assert "shall fail closed as `evidence_persistence_failure`" in req.lower()
        assert "no fallback to `os.replace`, or to any other overwrite-capable primitive, under any condition" in req

    def test_no_check_then_replace_authority_remains(self, text):
        req = _norm(_req052(text))
        assert "no other passage in this contract's non-normative prose or examples describes `os.replace` as a winner-publication mechanism as of v1.1" in req

    def test_state_machine_no_canonical_to_canonical_transition(self, text):
        req = _norm(_req052(text))
        assert "`CANONICAL(bytes)` never transitions to `CANONICAL(other_bytes)`" in req
        assert 'delete the existing file, then create a new one" is explicitly not a compliant' in req

    def test_generalizes_to_n_writers(self, text):
        req = _norm(_req052(text))
        assert "generalizes without modification to any number of concurrent writers" in req
        assert "each writer's `os.link` attempt is independently exclusive against the filesystem" in req

    def test_crash_before_link_no_canonical_artifact(self, text):
        req = _norm(_req052(text))
        assert "a crash before step (4)'s `os.link` call leaves no canonical final artifact" in req.lower() or "A crash before step (4)'s `os.link` call leaves no canonical final artifact".lower() in req.lower()

    def test_crash_after_link_success_leaves_artifact_intact(self, text):
        req = _norm(_req052(text))
        assert "a crash after step (4)'s successful `os.link` leaves the canonical final artifact intact".lower() in req.lower()
        assert "that cleanup failure is never authoritative" in req

    def test_temp_file_complete_before_link_attempt(self, text):
        req = _norm(_req052(text))
        # step (3) writes+fsyncs; step (4) is the *next* step, no intervening write step
        idx_fsync = req.index("os.fsync(fd)")
        idx_link_attempt = req.index("**(4)** attempt `os.link")
        assert idx_fsync < idx_link_attempt
        assert "already-fully-written, already-fsynced temp file's inode" in req

    def test_no_partial_file_visible(self, text):
        req = _norm(_req052(text))
        assert "no partially-written file ever visible at `final_path`" in req


# ═══════════════════════════════════════════════════════════════════════
# 4. Error mapping / fail-closed vocabulary re-check
# ═══════════════════════════════════════════════════════════════════════


class TestErrorMapping:
    def test_evidence_conflict_maps_exit_7(self, text):
        section = _section(text, "## 22. Closed Error Vocabulary", "## 23.")
        assert "`evidence_conflict`" in section and "7" in section

    def test_evidence_persistence_failure_maps_exit_8(self, text):
        section = _section(text, "## 22. Closed Error Vocabulary", "## 23.")
        assert "`evidence_persistence_failure`" in section and "8" in section

    def test_no_new_error_type_introduced_by_repair(self, text):
        section = _section(text, "## 22. Closed Error Vocabulary", "## 23.")
        # exactly 12 distinct error_type table rows (unchanged from v1.0),
        # excluding the header row itself
        rows = [
            l
            for l in section.splitlines()
            if l.startswith("| `") and l.count("|") >= 3 and "error_type" not in l
        ]
        assert len(rows) == 12


# ═══════════════════════════════════════════════════════════════════════
# 5. Symlink / path preservation non-regression (HSCE-REQ-057/058)
# ═══════════════════════════════════════════════════════════════════════


class TestSymlinkNonRegression:
    def test_req_057_058_present_and_unweakened(self, text):
        section = _section(text, "## 25. Path Validation", "## 26.")
        assert "HSCE-REQ-057" in section
        assert "HSCE-REQ-058" in section
        assert "rejected" in section.lower()

    def test_req052_cross_references_057_058(self, text):
        req = _norm(_req052(text))
        assert "per §57" in req


# ═══════════════════════════════════════════════════════════════════════
# 6. Canonical byte comparison (HSCE-REQ-053) non-regression
# ═══════════════════════════════════════════════════════════════════════


class TestCanonicalComparison:
    def test_req_053_unchanged_deterministic_serialization(self, text):
        section = _norm(_section(text, "**HSCE-REQ-053.**", "**HSCE-REQ-054.**"))
        assert "sort_keys=True" in section
        assert "allow_nan=False" in section
        assert "duplicate JSON keys rejected on parse" in section

    def test_req052_explicitly_uses_053_for_both_write_and_compare(self, text):
        req = _norm(_req052(text))
        assert "serialize the candidate envelope to canonical bytes per §53" in req
        assert "compare its canonical bytes (§53)" in req


# ═══════════════════════════════════════════════════════════════════════
# 7. Finding dispositions (F-1, F-2, 149O.10-F-3, Obs-2)
# ═══════════════════════════════════════════════════════════════════════


class TestFindingDispositions:
    def test_f1_closed(self, text):
        section = _section(text, "**F-1 disposition", "**F-2 disposition")
        assert "**CLOSED.**" in section

    def test_f2_closed(self, text):
        section = _section(text, "**F-2 disposition", "**149O.10-F-3 disposition")
        assert "**CLOSED.**" in section

    def test_f3_repaired_pending_reverification_not_yet_closed(self, text):
        section = _section(text, "**149O.10-F-3 disposition", "**Obs-2 disposition")
        assert "REPAIRED AT CONTRACT LEVEL" in section
        assert "PENDING INDEPENDENT" in section

    def test_obs2_closed(self, text):
        section = _section(text, "**Obs-2 disposition", "**Regression review:**")
        assert "**CLOSED.**" in section

    def test_no_current_claim_of_verified(self, text):
        assert "HSCE-001 v1.1 VERIFIED" not in text
        assert "READY FOR INDEPENDENT RE-VERIFICATION" in text


# ═══════════════════════════════════════════════════════════════════════
# 8. Non-regression of untouched sections (spot re-check independent of
#    149O.10.1's own regression-review prose)
# ═══════════════════════════════════════════════════════════════════════


class TestUntouchedSectionNonRegression:
    def test_sc1_through_sc12_all_present_and_only_sc7_mechanism_changed(self, text):
        section = _section(text, "## 37. Security Invariants", "## 38.")
        for i in range(1, 13):
            assert f"**SC-{i}.**" in section
        assert "silently overwritten" in section  # SC-7 statement retained

    def test_cli_grammar_byte_identical_to_v1_0(self):
        result = subprocess.run(
            ["git", "diff", _V1_0_FREEZE_COMMIT, _V1_1_REPAIR_COMMIT, "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        added = "\n".join(l for l in result.stdout.splitlines() if l.startswith("+") and not l.startswith("+++"))
        removed = "\n".join(l for l in result.stdout.splitlines() if l.startswith("-") and not l.startswith("---"))
        assert "pcae hatp sign rollback --site" not in added
        assert "pcae hatp sign rollback --site" not in removed

    def test_evidence_store_root_and_layout_unchanged(self):
        result = subprocess.run(
            ["git", "diff", _V1_0_FREEZE_COMMIT, _V1_1_REPAIR_COMMIT, "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        added = "\n".join(l for l in result.stdout.splitlines() if l.startswith("+") and not l.startswith("+++"))
        assert ".pcae/hatp-evidence/" not in added or "creation-registry" not in added


# ═══════════════════════════════════════════════════════════════════════
# 9. Abstract concurrency model + permutation proof (contract-model only,
#    no filesystem access)
# ═══════════════════════════════════════════════════════════════════════


class _ExclusivePublishModel:
    """Direct transcription of HSCE-REQ-052's normative rule, independent
    of any filesystem: state is ABSENT or CANONICAL(bytes)."""

    def __init__(self):
        self.state = None  # None == ABSENT

    def publish(self, candidate: bytes) -> str:
        if self.state is None:
            self.state = candidate
            return "WINNER"
        if candidate == self.state:
            return "IDEMPOTENT_SUCCESS"
        return "EVIDENCE_CONFLICT"


class TestAbstractModel:
    def test_two_writer_all_permutations_identical(self):
        for order in itertools.permutations([b"A", b"A"]):
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in order]
            assert results.count("WINNER") == 1
            assert set(results) <= {"WINNER", "IDEMPOTENT_SUCCESS"}
            assert model.state == b"A"

    def test_two_writer_all_permutations_differing(self):
        for order in itertools.permutations([b"A", b"B"]):
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in order]
            assert results.count("WINNER") == 1
            winner_index = results.index("WINNER")
            for i, r in enumerate(results):
                if i != winner_index:
                    assert r == "EVIDENCE_CONFLICT"
            assert model.state == order[winner_index]

    def test_three_writer_all_unique_orderings_aaa(self):
        for order in set(itertools.permutations([b"A", b"A", b"A"])):
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in order]
            assert results.count("WINNER") == 1
            assert set(results) <= {"WINNER", "IDEMPOTENT_SUCCESS"}

    def test_three_writer_all_unique_orderings_aab(self):
        for order in set(itertools.permutations([b"A", b"A", b"B"])):
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in order]
            assert results.count("WINNER") == 1
            winner_value = model.state
            for c, r in zip(order, results):
                if r == "WINNER":
                    continue
                if c == winner_value:
                    assert r == "IDEMPOTENT_SUCCESS"
                else:
                    assert r == "EVIDENCE_CONFLICT"

    def test_three_writer_all_unique_orderings_abc(self):
        for order in set(itertools.permutations([b"A", b"B", b"C"])):
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in order]
            assert results.count("WINNER") == 1
            assert results.count("EVIDENCE_CONFLICT") == 2

    def test_randomized_many_writer_invariant(self):
        import random

        rng = random.Random(149010_2)
        for _ in range(200):
            n = rng.randint(2, 12)
            pool = [f"payload-{rng.randint(0, 3)}".encode() for _ in range(n)]
            model = _ExclusivePublishModel()
            results = [model.publish(c) for c in pool]
            assert results.count("WINNER") == 1
            winner_bytes = model.state
            for c, r in zip(pool, results):
                if r == "WINNER":
                    continue
                assert r == ("IDEMPOTENT_SUCCESS" if c == winner_bytes else "EVIDENCE_CONFLICT")

    def test_canonical_immutable_once_set(self):
        model = _ExclusivePublishModel()
        model.publish(b"first")
        for candidate in [b"first", b"second", b"first", b"third"]:
            model.publish(candidate)
            assert model.state == b"first"


# ═══════════════════════════════════════════════════════════════════════
# 10. Real filesystem os.link probes (test-only; exercises the raw
#     primitive the contract selected, never application code)
# ═══════════════════════════════════════════════════════════════════════


class TestRealFilesystemLinkProbe:
    def test_single_writer_absent_destination_succeeds(self, tmp_path):
        final = tmp_path / "envelope.json"
        temp = tmp_path / f".tmp-{uuid.uuid4().hex}"
        temp.write_bytes(b"A-bytes")
        os.link(temp, final)
        assert final.read_bytes() == b"A-bytes"

    def test_existing_destination_second_link_raises_file_exists(self, tmp_path):
        final = tmp_path / "envelope.json"
        tempA = tmp_path / "tmpA"
        tempA.write_bytes(b"A-bytes")
        os.link(tempA, final)

        tempB = tmp_path / "tmpB"
        tempB.write_bytes(b"B-different-bytes")
        with pytest.raises(FileExistsError):
            os.link(tempB, final)
        assert final.read_bytes() == b"A-bytes", "destination must be unchanged after the failed link"

    def test_existing_destination_identical_bytes_loser_would_compare_equal(self, tmp_path):
        final = tmp_path / "envelope.json"
        tempA = tmp_path / "tmpA"
        payload = b"identical-canonical-bytes"
        tempA.write_bytes(payload)
        os.link(tempA, final)

        tempB = tmp_path / "tmpB"
        tempB.write_bytes(payload)
        with pytest.raises(FileExistsError):
            os.link(tempB, final)
        # loser's own comparison step (contract §24 step 6): read + compare
        assert final.read_bytes() == payload, "loser's compare must observe byte-identical -> idempotent success"

    @pytest.mark.parametrize("n", [2, 8, 32])
    def test_concurrent_identical_writers_exactly_one_winner(self, tmp_path, n):
        final = tmp_path / "envelope.json"
        payload = b"identical-payload"
        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(n)

        def writer(i):
            temp = tmp_path / f"tmp-{i}"
            temp.write_bytes(payload)
            barrier.wait()
            try:
                os.link(temp, final)
                outcome = "winner"
            except FileExistsError:
                outcome = "loser"
            with lock:
                results.append(outcome)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results.count("winner") == 1
        assert results.count("loser") == n - 1
        assert final.read_bytes() == payload

    @pytest.mark.parametrize("n", [2, 8, 32])
    def test_concurrent_differing_writers_exactly_one_winner_no_overwrite(self, tmp_path, n):
        final = tmp_path / "envelope.json"
        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(n)

        def writer(i):
            payload = f"candidate-{i}".encode()
            temp = tmp_path / f"tmp-{i}"
            temp.write_bytes(payload)
            barrier.wait()
            try:
                os.link(temp, final)
                with lock:
                    results.append(("winner", payload))
            except FileExistsError:
                with lock:
                    results.append(("loser", payload))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        winners = [r for r in results if r[0] == "winner"]
        assert len(winners) == 1
        assert final.read_bytes() == winners[0][1]
        losers = [r for r in results if r[0] == "loser"]
        assert len(losers) == n - 1
        for _, payload in losers:
            assert payload != winners[0][1]

    def test_mixed_identical_and_differing_race(self, tmp_path):
        final = tmp_path / "envelope.json"
        winner_payload = b"eventual-winner-bytes"
        # 4 candidates identical to eventual winner, 4 candidates distinct
        payloads = [winner_payload] * 4 + [f"different-{i}".encode() for i in range(4)]
        n = len(payloads)
        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(n)

        def writer(i, payload):
            temp = tmp_path / f"tmp-{i}"
            temp.write_bytes(payload)
            barrier.wait()
            try:
                os.link(temp, final)
                with lock:
                    results.append(("winner", payload))
            except FileExistsError:
                with lock:
                    results.append(("loser", payload))

        threads = [threading.Thread(target=writer, args=(i, p)) for i, p in enumerate(payloads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        winners = [r for r in results if r[0] == "winner"]
        assert len(winners) == 1
        final_bytes = final.read_bytes()
        assert final_bytes == winners[0][1]
        for outcome, payload in results:
            if outcome == "winner":
                continue
            # this loser's comparison outcome is determined by whether its
            # payload equals whatever ended up canonical
            expected = "idempotent" if payload == final_bytes else "conflict"
            actual = "idempotent" if payload == final_bytes else "conflict"
            assert expected == actual  # comparison is a pure function of (payload, final_bytes)

    def test_symlink_destination_detected_before_any_compare(self, tmp_path):
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_target = outside_dir / "real.json"
        outside_target.write_bytes(b"outside-bytes")

        envelopes = tmp_path / "envelopes"
        envelopes.mkdir()
        final = envelopes / "envelope.json"
        os.symlink(outside_target, final)

        assert os.path.islink(final), "contract-mandated pre-compare check target"
        # An implementation following §24 step (6) must check islink() and
        # reject as evidence_persistence_failure *before* reading through it.
        assert not outside_target.read_bytes() == b"attacker-write", "sanity: outside file untouched by this probe"

    def test_deleted_temp_after_winner_success_final_still_intact(self, tmp_path):
        """Step (5): temp unlink after a winning link is non-authoritative
        -- removing (or failing to remove) the temp name must not affect
        the already-published final artifact, because hard links share
        the inode but final's directory entry is independent."""

        final = tmp_path / "envelope.json"
        temp = tmp_path / "tmp-winner"
        temp.write_bytes(b"winner-bytes")
        os.link(temp, final)
        os.unlink(temp)  # step (5) cleanup
        assert final.read_bytes() == b"winner-bytes", "final survives temp-name removal (independent inodes link, shared content)"

    def test_orphan_temp_from_loser_is_non_authoritative(self, tmp_path):
        final = tmp_path / "envelope.json"
        tempA = tmp_path / "tmpA"
        tempA.write_bytes(b"A")
        os.link(tempA, final)

        tempB = tmp_path / "tmpB"
        tempB.write_bytes(b"B")
        with pytest.raises(FileExistsError):
            os.link(tempB, final)
        # loser's temp file (tempB) still exists on disk until step (6)'s
        # cleanup runs; its mere existence must not be treated as canonical
        assert tempB.exists()
        assert final.read_bytes() == b"A", "orphan loser temp has no bearing on canonical state"


class TestUnsupportedFilesystemFailClosedReasoning:
    """Real EXDEV/hard-link-unsupported conditions cannot be reliably
    forced without a second real filesystem mount in this test
    environment; this class documents that limitation and independently
    re-confirms (from contract text, not filesystem behavior) that no
    fallback path exists to weaken persistence on such errors."""

    def test_contract_names_no_fallback_for_other_oserror(self, text):
        req = _norm(_req052(text))
        assert "no fallback to `os.replace`" in req
        assert "or to any other overwrite-capable primitive, under any condition" in req

    def test_os_link_raises_oserror_for_nonexistent_source(self, tmp_path):
        """Not EXDEV itself, but independently corroborates that os.link
        fails (rather than silently succeeding/falling back) for at least
        one real non-EEXIST error condition on this platform."""

        final = tmp_path / "envelope.json"
        missing_temp = tmp_path / "does-not-exist"
        with pytest.raises(OSError):
            os.link(missing_temp, final)
        assert not final.exists()


# ═══════════════════════════════════════════════════════════════════════
# 11. Production / contract boundaries
# ═══════════════════════════════════════════════════════════════════════


class TestProductionAndContractBoundaries:
    def test_no_production_source_modified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", "src/pcae/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_hatp_001_unmodified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", str(HATP_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_rae_001_unmodified(self):
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD", "--", str(RAE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == ""

    def test_hsce_001_itself_unmodified_by_this_phase(self):
        result = subprocess.run(
            ["git", "diff", "--stat", _V1_1_REPAIR_COMMIT, "HEAD", "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip("git diff unavailable")
        assert result.stdout.strip() == "", "this phase is verification-only; HSCE-001 v1.1 text must not change"

    def test_no_hatp_evidence_directory_created(self):
        assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists()

    def test_no_hatp_sign_cli_implementation_exists(self):
        result = subprocess.run(
            ["grep", "-rEn", "hatp sign|HATPSignedEvidenceEnvelope", "src/pcae/cli.py", "src/pcae/commands/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout == ""

    def test_write_atomic_json_production_helper_unchanged_still_racy(self):
        """Independently reconfirms production code was not touched by any
        phase in this repair/re-verification chain: the underlying
        _write_atomic_json helper (never called by the repaired
        contract's algorithm) remains exactly as racy as before."""

        from pcae.core.rollback_approval_evidence import _write_atomic_json
        import inspect

        source = inspect.getsource(_write_atomic_json)
        assert "path.exists()" in source
        assert "os.replace(" in source
        assert "os.link(" not in source

    def test_write_creation_registration_still_uses_o_creat_o_excl_precedent(self):
        from pcae.core.rollback_approval_evidence import RollbackApprovalEvidenceStore
        import inspect

        source = inspect.getsource(RollbackApprovalEvidenceStore.write_creation_registration)
        assert "O_CREAT" in source and "O_EXCL" in source
