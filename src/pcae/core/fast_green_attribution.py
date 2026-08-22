"""Attribution-aware Fast Green verification — Phase 149O.20L.7O.2R.

Implements the structured ``fast_green`` evidence path frozen by
149O.20L.7O.2Q (``docs/PHASE_149O_20L_7O_2Q_ATTRIBUTION_AWARE_VERIFICATION_
GATE_ARCHITECTURE.md``) and corrected by 149O.20L.7O.2Q.1
(``docs/PHASE_149O_20L_7O_2Q_1_QUARANTINED_ANCESTOR_PUSH_STATE_AND_
ATTRIBUTION_GATE_CONTRACT_RECONCILIATION.md``).

This module is additive: it does not modify ``_fast_green_failure_signal()``
or the scalar `fast_green` acceptance behavior in ``phase_reports.py``. It
introduces a second, structured evidence shape and its own validator,
wired into ``validate_derived_correctness()`` as a parallel path selected
only when ``test_results["fast_green"]`` is a ``dict`` carrying the
structured schema marker.

Trust model (honest statement, per 2Q design Section 17 / 2Q.1 Section 28):
this is *procedural* provenance (a content digest tying the persisted
evidence artifact to the report's inline claim), not cryptographic
tamper-evidence — no signing key is involved. It closes the "hand-typed
attribution counts" failure mode (134E.9.1's shape, generalized) by
requiring a real evidence artifact whose classification the validator
*recomputes independently* from the raw node-ID sets, rather than trusting
the artifact's own bucket labels for the load-bearing ``attributable`` and
``excluded_preexisting`` buckets. A actor with direct filesystem write
access to ``.pcae/`` could still forge the artifact; that is true of every
other trust field in this repository's governance model and is not a new
weakness this phase introduces.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "fast_green_attribution.v1"

# Section 2Q.1 §12 — "some bounded, evidence-backed policy is required, not
# open-ended agent discretion". 2Q.1 explicitly left the exact numeric bound
# unfrozen; this implementation phase picks a small, documented bound. A
# future governed phase may revisit this constant.
ENVIRONMENT_EXCLUSION_BOUND = 3

# The exact, closed test-identity recognized for the push-ceremony artifact
# case (2Q.1 §13, §20). Matched against the test *function name* portion of
# a pytest node ID (after the final "::"), not the full node ID, so it is
# recognized regardless of which per-phase test module defines it.
EXPECTED_ARTIFACT_TEST_NAME = "test_head_equals_origin_main"

# Literal pushed_status values that mean "already pushed" — frozen exactly
# by project_phase_completion_procedure.md / phase_reports.py's own
# assess_completeness() check.
_PUSHED_LITERALS = ("pushed", "clean", "nothing_to_push")

ARTIFACT_DIR_NAME = os.path.join(".pcae", "fast-green-attribution")

_PHASE_COMMIT_SUBJECT_RE = re.compile(r"^Phase\s+(\S+?)\s*[:—–-]")

# The exact governed Fast Green selection (pyproject.toml comment, "Test
# tiers (Phase 88N.5)"), minus ``-n auto``: baseline and candidate runs here
# always execute sequentially (see module docstring / final report for why),
# but both sides always use this identical command list — never optimized
# or narrowed for one side only (2Q.1 §17).
FAST_GREEN_PYTEST_ARGS: tuple[str, ...] = ("-m", "fast_green", "-q", "--no-header")

_COLLECTOR_PLUGIN_SOURCE = '''
import json
import os


class _PcaeFastGreenCollector:
    def __init__(self):
        self.results = {"passed": [], "failed": [], "errors": []}

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            if report.passed:
                self.results["passed"].append(report.nodeid)
            elif report.failed:
                self.results["failed"].append(report.nodeid)
        elif report.when in ("setup", "teardown") and report.failed:
            self.results["errors"].append(report.nodeid)

    def pytest_collectreport(self, report):
        if report.failed:
            self.results["errors"].append(report.nodeid or "<collection>")

    def pytest_sessionfinish(self, session, exitstatus):
        out_path = os.environ.get("PCAE_FG_OUTPUT")
        if out_path:
            with open(out_path, "w") as fh:
                json.dump(self.results, fh)


def pytest_configure(config):
    config.pluginmanager.register(_PcaeFastGreenCollector(), "pcae-fg-collector")
'''


class AttributionError(RuntimeError):
    """Raised when the controlled comparison itself cannot be produced."""


@dataclass
class RawResult:
    failed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_set(self) -> set[str]:
        return set(self.failed) | set(self.errors)

    def to_dict(self) -> dict[str, list[str]]:
        return {"failed": sorted(self.failed), "errors": sorted(self.errors)}


def _run(cmd: list[str], cwd: str, timeout: int = 60, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, timeout=timeout, shell=False, env=env,
    )


def _git(repo_root: str, *args: str, timeout: int = 30) -> str:
    proc = _run(["git", *args], cwd=repo_root, timeout=timeout)
    if proc.returncode != 0:
        raise AttributionError(
            f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout.decode("utf-8", "replace").strip()


def resolve_repo_root(start: str) -> str:
    """Canonical repository root for `start` (defaults to itself if `git`
    cannot resolve one, e.g. in a unit test with no real repo)."""
    proc = _run(["git", "rev-parse", "--show-toplevel"], cwd=start, timeout=10)
    if proc.returncode == 0:
        return proc.stdout.decode("utf-8", "replace").strip()
    return start


def current_head(repo_root: str) -> str:
    """Exact current HEAD SHA. Fetches nothing — caller's responsibility
    (2Q.1 §28: 'stale origin/main assumptions' concerns origin comparisons,
    not HEAD, which must reflect the literal local candidate)."""
    return _git(repo_root, "rev-parse", "HEAD")


def derive_phase_entry_baseline(repo_root: str, phase_id: str) -> tuple[str, str]:
    """Programmatically derive the authoritative baseline commit (2Q.1 §9).

    Baseline = parent of the oldest commit whose subject line is attributed
    to ``phase_id`` (``"Phase <phase_id>: ..."``). Never a caller-supplied
    argument in the authoritative path — this function takes no override.

    Returns ``(baseline_sha, method)`` where ``method`` documents how the
    baseline was derived (for the evidence artifact and human report).
    """
    log = _git(
        repo_root, "log", "--reverse", "--format=%H%x1f%s", "HEAD",
    )
    first_commit: str | None = None
    for line in log.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        match = _PHASE_COMMIT_SUBJECT_RE.match(subject)
        if match and match.group(1).strip().upper() == phase_id.strip().upper():
            first_commit = sha
            break
    if first_commit is None:
        # No commit attributed to this phase exists yet on HEAD's ancestry —
        # the phase has not started committing. Baseline collapses to HEAD:
        # a degenerate but honest comparison (raw_failures == baseline's own
        # raw failures, so every node is preexisting by construction).
        head = current_head(repo_root)
        return head, "no_phase_commits_found_baseline_collapses_to_head"
    parents = _git(repo_root, "rev-list", "--parents", "-n", "1", first_commit)
    parts = parents.split()
    if len(parts) < 2:
        # First commit attributed to the phase has no parent (root commit) —
        # cannot compute a meaningful diff; treat baseline as itself (all
        # raw failures unclassifiable except preexisting-against-itself).
        return first_commit, "phase_first_commit_is_root_no_parent"
    return parts[1], "parent_of_oldest_phase_attributed_commit"


def _canonical_digest(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


class _IsolatedWorktree:
    """RAII-style isolated git worktree at an exact commit SHA.

    Used for *both* baseline and candidate runs so the two sides execute
    under an equivalent, uncontaminated environment (2Q.1 §8, §17; the
    cross-tree PYTHONPATH contamination bug discovered in Phase 2P).
    """

    def __init__(self, repo_root: str, commit_sha: str):
        self.repo_root = repo_root
        self.commit_sha = commit_sha
        self.path: str | None = None

    def __enter__(self) -> str:
        self.path = tempfile.mkdtemp(prefix="pcae-fga-wt-")
        # mkdtemp creates the dir; `git worktree add` needs to populate an
        # existing-but-empty or nonexistent path — remove it first so git
        # doesn't refuse a non-empty check on some git versions.
        shutil.rmtree(self.path)
        proc = _run(
            ["git", "worktree", "add", "--detach", self.path, self.commit_sha],
            cwd=self.repo_root, timeout=60,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", "replace").strip()
            raise AttributionError(f"git worktree add failed for {self.commit_sha}: {stderr}")
        return self.path

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.path is None:
            return
        try:
            _run(
                ["git", "worktree", "remove", "--force", self.path],
                cwd=self.repo_root, timeout=30,
            )
        except Exception:
            pass
        finally:
            if os.path.isdir(self.path):
                shutil.rmtree(self.path, ignore_errors=True)


def _collect_raw_result(worktree_path: str, timeout: int = 900) -> RawResult:
    """Execute the governed Fast Green selection inside `worktree_path`,
    isolated from any other checkout's `pcae` source via PYTHONPATH.
    """
    plugin_dir = tempfile.mkdtemp(prefix="pcae-fga-plugin-")
    try:
        plugin_path = os.path.join(plugin_dir, "pcae_fg_collector_plugin.py")
        with open(plugin_path, "w") as fh:
            fh.write(_COLLECTOR_PLUGIN_SOURCE)

        output_fd, output_path = tempfile.mkstemp(prefix="pcae-fga-result-", suffix=".json")
        os.close(output_fd)

        src_dir = os.path.join(worktree_path, "src")
        env = os.environ.copy()
        # Contamination fix (Phase 2P defect): the worktree's own `src/`
        # must precede any editable-install path already on PYTHONPATH so
        # `import pcae` resolves to the worktree's source, not whatever
        # checkout the ambient environment happens to have installed.
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (plugin_dir, src_dir, existing) if p
        )
        env["PCAE_FG_OUTPUT"] = output_path
        env["PCAE_NOTIFY_CONFIG_DISABLE"] = "1"
        for key in (
            "PCAE_NOTIFY_ENABLED", "PCAE_NOTIFY_SINKS",
            "PCAE_TELEGRAM_ENABLED", "PCAE_TELEGRAM_BOT_TOKEN",
            "PCAE_TELEGRAM_CHAT_ID",
        ):
            env.pop(key, None)

        cmd = [
            sys.executable, "-m", "pytest",
            *FAST_GREEN_PYTEST_ARGS,
            "-p", "pcae_fg_collector_plugin",
        ]
        try:
            proc = _run(cmd, cwd=worktree_path, timeout=timeout, env=env)
        except subprocess.TimeoutExpired as exc:
            raise AttributionError(
                f"fast_green collection timed out after {timeout}s in {worktree_path}"
            ) from exc

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            stderr_tail = proc.stderr.decode("utf-8", "replace")[-2000:]
            raise AttributionError(
                "fast_green collection produced no result file (pytest may have "
                f"crashed before session finish); exit={proc.returncode}; "
                f"stderr tail: {stderr_tail!r}"
            )
        with open(output_path) as fh:
            raw = json.load(fh)
        return RawResult(failed=list(raw.get("failed", [])), errors=list(raw.get("errors", [])))
    finally:
        shutil.rmtree(plugin_dir, ignore_errors=True)
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass


def _rerun_single_node(worktree_path: str, node_id: str, timeout: int = 120) -> str:
    """Run exactly one node ID in isolation. Returns "pass", "fail", or
    "error" (setup/teardown failure / non-assertion signal)."""
    plugin_dir = tempfile.mkdtemp(prefix="pcae-fga-rerun-plugin-")
    try:
        plugin_path = os.path.join(plugin_dir, "pcae_fg_collector_plugin.py")
        with open(plugin_path, "w") as fh:
            fh.write(_COLLECTOR_PLUGIN_SOURCE)
        output_fd, output_path = tempfile.mkstemp(prefix="pcae-fga-rerun-", suffix=".json")
        os.close(output_fd)

        src_dir = os.path.join(worktree_path, "src")
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(p for p in (plugin_dir, src_dir, existing) if p)
        env["PCAE_FG_OUTPUT"] = output_path
        env["PCAE_NOTIFY_CONFIG_DISABLE"] = "1"

        cmd = [sys.executable, "-m", "pytest", node_id, "-q", "--no-header", "-p", "pcae_fg_collector_plugin"]
        try:
            _run(cmd, cwd=worktree_path, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return "error"
        if not os.path.exists(output_path):
            return "error"
        with open(output_path) as fh:
            raw = json.load(fh)
        if node_id in raw.get("passed", []):
            return "pass"
        if node_id in raw.get("errors", []):
            return "error"
        return "fail"
    finally:
        shutil.rmtree(plugin_dir, ignore_errors=True)
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass


def _test_function_name(node_id: str) -> str:
    return node_id.rsplit("::", 1)[-1]


def build_attribution_evidence(
    repo_root: str,
    phase_id: str,
    pushed_status: str,
    rerun_node_ids: list[str] | None = None,
    candidate_commit: str | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    """Perform the controlled baseline-vs-candidate comparison and produce
    the Section 5 structured evidence dict (not yet persisted).

    `rerun_node_ids` is the caller's *explicit, bounded* request for which
    currently-failing nodes should be given an isolated single-node rerun
    for possible `excluded_environment_failures` classification (2Q.1 §12
    — never automatic, never unbounded).
    """
    candidate = candidate_commit or current_head(repo_root)
    baseline, baseline_method = derive_phase_entry_baseline(repo_root, phase_id)

    with _IsolatedWorktree(repo_root, baseline) as baseline_wt:
        baseline_raw = _collect_raw_result(baseline_wt, timeout=timeout)

    # Re-check freshness before the (potentially long) candidate run even
    # starts — if HEAD already moved past what the caller asked us to
    # certify, fail fast rather than certifying a stale SHA.
    if current_head(repo_root) != candidate:
        raise AttributionError(
            f"HEAD moved during baseline capture (expected candidate {candidate!r}); "
            "rerun this command against the new HEAD."
        )

    with _IsolatedWorktree(repo_root, candidate) as candidate_wt:
        candidate_raw = _collect_raw_result(candidate_wt, timeout=timeout)

    if current_head(repo_root) != candidate:
        raise AttributionError(
            f"HEAD moved during candidate capture (expected candidate {candidate!r}); "
            "rerun this command against the new HEAD."
        )

    candidate_set = candidate_raw.as_set()
    baseline_set = baseline_raw.as_set()
    preexisting_ids = sorted(candidate_set & baseline_set)

    remaining = candidate_set - set(preexisting_ids)

    environment_entries: list[dict[str, str]] = []
    if rerun_node_ids:
        bounded = list(dict.fromkeys(rerun_node_ids))[:ENVIRONMENT_EXCLUSION_BOUND]
        with _IsolatedWorktree(repo_root, candidate) as rerun_wt:
            for node_id in bounded:
                if node_id not in remaining:
                    continue
                rerun_result = _rerun_single_node(rerun_wt, node_id, timeout=180)
                if rerun_result == "pass":
                    environment_entries.append({
                        "node_id": node_id,
                        "rerun_result": "pass",
                        "rerun_at": datetime.now(timezone.utc).isoformat(),
                        "rerun_commit": candidate,
                    })
                elif rerun_result == "error":
                    environment_entries.append({
                        "node_id": node_id,
                        "rerun_result": "divergent_error",
                        "rerun_at": datetime.now(timezone.utc).isoformat(),
                        "rerun_commit": candidate,
                    })
                # "fail" (identical failure) qualifies for nothing; stays in
                # `remaining` and defaults to attributable (2Q.1 §12).

    environment_ids = {e["node_id"] for e in environment_entries}
    remaining -= environment_ids

    expected_entries: list[dict[str, str]] = []
    if pushed_status not in _PUSHED_LITERALS:
        for node_id in sorted(remaining):
            if _test_function_name(node_id) == EXPECTED_ARTIFACT_TEST_NAME:
                expected_entries.append({
                    "node_id": node_id,
                    "predicted_by": "pushed_status",
                    "predicted_value": pushed_status,
                })
    expected_ids = {e["node_id"] for e in expected_entries}
    remaining -= expected_ids

    attributable_ids = sorted(remaining)

    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "method": "baseline_vs_candidate_isolated_worktree",
        "baseline_commit": baseline,
        "baseline_method": baseline_method,
        "candidate_commit": candidate,
        "command": " ".join([sys.executable, "-m", "pytest", *FAST_GREEN_PYTEST_ARGS]),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_raw_failed": sorted(baseline_raw.failed),
        "baseline_raw_errors": sorted(baseline_raw.errors),
        "raw_failed": sorted(candidate_raw.failed),
        "raw_errors": sorted(candidate_raw.errors),
        "attributable_failures": attributable_ids,
        "excluded_preexisting_failures": [
            {"node_id": nid, "baseline_commit": baseline, "baseline_evidence": "failed_in_baseline"}
            for nid in preexisting_ids
        ],
        "excluded_environment_failures": environment_entries,
        "expected_phase_artifacts": expected_entries,
    }
    return evidence


def persist_evidence(repo_root: str, evidence: dict[str, Any]) -> dict[str, Any]:
    """Write `evidence` to a content-addressed artifact file and return the
    provenance-bearing structured `fast_green` value (evidence + provenance
    pointer) meant to be embedded verbatim as
    `test_results["fast_green"]`.
    """
    digest_payload = {k: v for k, v in evidence.items()}
    digest = _canonical_digest(digest_payload)
    artifact_dir = os.path.join(repo_root, ARTIFACT_DIR_NAME)
    os.makedirs(artifact_dir, exist_ok=True)
    artifact_rel = os.path.join(ARTIFACT_DIR_NAME, f"{digest}.json")
    artifact_abs = os.path.join(repo_root, artifact_rel)
    with open(artifact_abs, "w") as fh:
        json.dump(digest_payload, fh, sort_keys=True, indent=2)
        fh.write("\n")

    result = dict(evidence)
    result["provenance"] = {
        "generated_by_command": "pcae phase fast-green-attribution",
        "artifact_path": artifact_rel,
        "artifact_digest": digest,
    }
    return result


# ---------------------------------------------------------------------
# Validation (consumed by phase_reports.validate_derived_correctness)
# ---------------------------------------------------------------------

_REQUIRED_EVIDENCE_KEYS = (
    "method", "baseline_commit", "candidate_commit", "command",
    "raw_failed", "raw_errors", "attributable_failures",
    "excluded_preexisting_failures", "excluded_environment_failures",
    "expected_phase_artifacts", "provenance",
)


def is_structured_fast_green(value: Any) -> bool:
    return isinstance(value, dict) and value.get("schema_version") == SCHEMA_VERSION


def validate_structured_fast_green(
    value: dict[str, Any],
    repo_root: str,
    phase_id: str,
    pushed_status: str,
) -> list[str]:
    """Validate a structured `fast_green` value. Returns issues; empty
    means the structured evidence independently satisfies every 2Q.1 §15
    acceptance criterion. Fails closed on any ambiguity, exactly like the
    scalar path (2Q design Section 6/2Q.1 Section 15's own explicit
    parity requirement)."""
    issues: list[str] = []

    for key in _REQUIRED_EVIDENCE_KEYS:
        if key not in value:
            issues.append(f"structured fast_green missing required key {key!r}")
    if issues:
        return issues

    provenance = value.get("provenance")
    if not isinstance(provenance, dict):
        issues.append("structured fast_green provenance must be an object")
        return issues
    artifact_rel = provenance.get("artifact_path")
    artifact_digest = provenance.get("artifact_digest")
    if not artifact_rel or not artifact_digest:
        issues.append("structured fast_green provenance missing artifact_path/artifact_digest")
        return issues

    # Machine-produced-evidence check (2Q.1 §8, §28 'hand-editing counts'):
    # the artifact file is the source of truth. Recompute its digest and
    # require it to match the claimed digest, and require every evidentiary
    # field embedded in the report to equal the persisted artifact's fields
    # byte-for-byte. A value with no matching artifact file, or one whose
    # persisted content hashes differently than claimed, is rejected —
    # placing attribution numbers directly into metadata prose, however
    # precise-looking, cannot satisfy this.
    artifact_abs = os.path.join(repo_root, artifact_rel)
    norm_artifact_rel = os.path.normpath(artifact_rel)
    if norm_artifact_rel.startswith("..") or os.path.isabs(artifact_rel):
        issues.append("structured fast_green artifact_path escapes repository root")
        return issues
    if not os.path.isfile(artifact_abs):
        issues.append(
            f"structured fast_green evidence artifact not found: {artifact_rel!r} "
            "(hand-authored attribution without a persisted machine-produced "
            "artifact is rejected)"
        )
        return issues
    try:
        with open(artifact_abs) as fh:
            persisted = json.load(fh)
    except (OSError, ValueError) as exc:
        issues.append(f"structured fast_green evidence artifact unreadable: {exc}")
        return issues

    recomputed_digest = _canonical_digest(persisted)
    if recomputed_digest != artifact_digest:
        issues.append(
            "structured fast_green evidence artifact digest mismatch — "
            "artifact content does not match its own claimed digest"
        )
        return issues

    inline_evidence_keys = [k for k in value.keys() if k != "provenance"]
    for key in inline_evidence_keys:
        if persisted.get(key) != value.get(key):
            issues.append(
                f"structured fast_green field {key!r} diverges from the "
                "persisted evidence artifact — inline value does not match "
                "machine-produced evidence"
            )
    if issues:
        return issues

    evidence = persisted

    # Freshness (2Q.1 §10).
    try:
        actual_head = current_head(repo_root)
    except AttributionError as exc:
        issues.append(f"could not determine current HEAD to check freshness: {exc}")
        return issues
    if evidence.get("candidate_commit") != actual_head:
        issues.append(
            f"structured fast_green evidence is stale — candidate_commit "
            f"{evidence.get('candidate_commit')!r} != current HEAD {actual_head!r}"
        )

    # Baseline authority (2Q.1 §9).
    try:
        expected_baseline, _method = derive_phase_entry_baseline(repo_root, phase_id)
    except AttributionError as exc:
        issues.append(f"could not derive authoritative baseline: {exc}")
        return issues
    if evidence.get("baseline_commit") != expected_baseline:
        issues.append(
            "structured fast_green baseline is not authoritative — evidence "
            f"baseline {evidence.get('baseline_commit')!r} does not match the "
            f"phase-entry baseline {expected_baseline!r} derived from Git history"
        )

    # Test-selection equivalence (2Q.1 §17) — both sides recorded the exact
    # same command; this module only ever produces one command shape, but a
    # tampered/foreign artifact could claim otherwise.
    expected_command = " ".join([sys.executable, "-m", "pytest", *FAST_GREEN_PYTEST_ARGS])
    if evidence.get("command") != expected_command:
        issues.append(
            "structured fast_green command does not match the governed Fast "
            "Green selection — candidate-only deselection or a foreign "
            "command is not permitted"
        )

    baseline_failed = evidence.get("baseline_raw_failed")
    baseline_errors = evidence.get("baseline_raw_errors")
    if not isinstance(baseline_failed, list) or not isinstance(baseline_errors, list):
        issues.append("structured fast_green evidence missing baseline raw result sets")
        return issues
    baseline_set = set(baseline_failed) | set(baseline_errors)

    raw_failed = evidence.get("raw_failed")
    raw_errors = evidence.get("raw_errors")
    if not isinstance(raw_failed, list) or not isinstance(raw_errors, list):
        issues.append("structured fast_green raw_failed/raw_errors must be lists")
        return issues
    raw_set = set(raw_failed) | set(raw_errors)
    if len(raw_failed) != len(set(raw_failed)) or len(raw_errors) != len(set(raw_errors)):
        issues.append("structured fast_green raw_failed/raw_errors contain duplicate node IDs")
    if set(raw_failed) & set(raw_errors):
        issues.append("structured fast_green raw_failed/raw_errors overlap (same node in both)")

    # Independently recompute preexisting/attributable — never trust the
    # artifact's own bucket labels for these two (2Q.1 §11, §14; §4's "no
    # human/agent judgment call permitted" for attributable specifically).
    preexisting_computed = raw_set & baseline_set

    preexisting_claimed = evidence.get("excluded_preexisting_failures")
    if not isinstance(preexisting_claimed, list):
        issues.append("structured fast_green excluded_preexisting_failures must be a list")
        return issues
    preexisting_claimed_ids: set[str] = set()
    for entry in preexisting_claimed:
        if not isinstance(entry, dict) or not entry.get("node_id") or not entry.get("baseline_evidence"):
            issues.append(f"malformed excluded_preexisting_failures entry: {entry!r}")
            continue
        nid = entry["node_id"]
        if entry.get("baseline_commit") != evidence.get("baseline_commit"):
            issues.append(
                f"excluded_preexisting_failures entry {nid!r} baseline_commit "
                "does not match the evidence's own baseline_commit"
            )
        if nid in preexisting_claimed_ids:
            issues.append(f"duplicate excluded_preexisting_failures node_id: {nid!r}")
        preexisting_claimed_ids.add(nid)
    if preexisting_claimed_ids != preexisting_computed:
        issues.append(
            "structured fast_green excluded_preexisting_failures does not "
            "match the recomputed baseline∩candidate node-ID set — "
            f"claimed={sorted(preexisting_claimed_ids)!r} "
            f"computed={sorted(preexisting_computed)!r}"
        )

    environment_claimed = evidence.get("excluded_environment_failures")
    if not isinstance(environment_claimed, list):
        issues.append("structured fast_green excluded_environment_failures must be a list")
        return issues
    if len(environment_claimed) > ENVIRONMENT_EXCLUSION_BOUND:
        issues.append(
            f"structured fast_green excluded_environment_failures exceeds the "
            f"bounded policy ({len(environment_claimed)} > {ENVIRONMENT_EXCLUSION_BOUND})"
        )
    environment_ids: set[str] = set()
    for entry in environment_claimed:
        if not isinstance(entry, dict):
            issues.append(f"malformed excluded_environment_failures entry: {entry!r}")
            continue
        nid = entry.get("node_id")
        rerun_result = entry.get("rerun_result")
        rerun_at = entry.get("rerun_at")
        rerun_commit = entry.get("rerun_commit")
        if not nid or rerun_result not in ("pass", "divergent_error") or not rerun_at:
            issues.append(
                f"excluded_environment_failures entry {entry!r} lacks required "
                "machine-evidence fields (node_id, rerun_result in "
                "{'pass','divergent_error'}, rerun_at)"
            )
            continue
        if rerun_commit != evidence.get("candidate_commit"):
            issues.append(
                f"excluded_environment_failures entry {nid!r} rerun_commit "
                "does not match the candidate commit under evidence"
            )
        if nid in environment_ids:
            issues.append(f"duplicate excluded_environment_failures node_id: {nid!r}")
        environment_ids.add(nid)

    expected_claimed = evidence.get("expected_phase_artifacts")
    if not isinstance(expected_claimed, list):
        issues.append("structured fast_green expected_phase_artifacts must be a list")
        return issues
    expected_ids: set[str] = set()
    for entry in expected_claimed:
        if not isinstance(entry, dict):
            issues.append(f"malformed expected_phase_artifacts entry: {entry!r}")
            continue
        nid = entry.get("node_id")
        predicted_by = entry.get("predicted_by")
        if predicted_by != "pushed_status":
            issues.append(
                f"expected_phase_artifacts entry {nid!r} has unrecognized "
                f"predicted_by {predicted_by!r} — only the closed "
                "'pushed_status' case is implemented"
            )
            continue
        if not nid or _test_function_name(str(nid)) != EXPECTED_ARTIFACT_TEST_NAME:
            issues.append(
                f"expected_phase_artifacts entry {nid!r} does not match the "
                f"closed test identity {EXPECTED_ARTIFACT_TEST_NAME!r}"
            )
            continue
        if pushed_status in _PUSHED_LITERALS:
            issues.append(
                f"expected_phase_artifacts entry {nid!r} claims the pre-push "
                f"HEAD==origin/main exclusion, but report pushed_status "
                f"{pushed_status!r} is already a pushed literal"
            )
            continue
        if entry.get("predicted_value") != pushed_status:
            issues.append(
                f"expected_phase_artifacts entry {nid!r} predicted_value "
                f"{entry.get('predicted_value')!r} does not match the "
                f"report's actual pushed_status {pushed_status!r}"
            )
            continue
        if nid in expected_ids:
            issues.append(f"duplicate expected_phase_artifacts node_id: {nid!r}")
        expected_ids.add(nid)

    if issues:
        return issues

    # Conservation (2Q.1 §7): disjointness + exact coverage.
    all_classified = preexisting_computed | environment_ids | expected_ids
    overlaps = []
    seen: dict[str, str] = {}
    for bucket_name, ids in (
        ("excluded_preexisting_failures", preexisting_computed),
        ("excluded_environment_failures", environment_ids),
        ("expected_phase_artifacts", expected_ids),
    ):
        for nid in ids:
            if nid in seen:
                overlaps.append(f"{nid!r} in both {seen[nid]!r} and {bucket_name!r}")
            seen[nid] = bucket_name
    if overlaps:
        issues.append("structured fast_green bucket membership overlaps: " + "; ".join(overlaps))

    attributable_computed = sorted(raw_set - all_classified)
    attributable_claimed = evidence.get("attributable_failures")
    if not isinstance(attributable_claimed, list):
        issues.append("structured fast_green attributable_failures must be a list")
        return issues
    if sorted(set(attributable_claimed)) != attributable_computed:
        issues.append(
            "structured fast_green attributable_failures does not match the "
            f"recomputed default set — claimed={sorted(set(attributable_claimed))!r} "
            f"computed={attributable_computed!r}"
        )

    unknown_in_buckets = all_classified - raw_set
    if unknown_in_buckets:
        issues.append(
            "structured fast_green classifies node ID(s) not present in "
            f"raw_failed/raw_errors: {sorted(unknown_in_buckets)!r}"
        )

    if issues:
        return issues

    if attributable_computed:
        issues.append(
            "structured fast_green has nonzero attributable_failures — "
            f"{attributable_computed!r} — cannot certify complete"
        )

    return issues
