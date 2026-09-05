"""Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R
— Production Protected-Presentation Registration Continuation Against
Existing Generation-1 Deployment State.

This suite verifies everything mechanically re-checkable without
administrator privilege: CPIPC successor validity, the immutable-Git
provenance and independently-recomputed digest of the generation-1
helper, independent recomputation of the verifier-configuration digest
via the repository's own canonical serialization, self-consistency of
the recorded post-registration digests (installation_digest,
anchor_digest, cross-record descriptor_digest/installation_digest
binding) against the durable evidence artifact, write-set confinement
against the derived authorized set, and that this phase introduced no
production/test/contract/dependency source change.

The actual privileged PPA registration transaction and its read-back
against the real root-owned, mode-0700
`/Library/Application Support/PCAE/HPAC/protected-root` tree were
performed once, out of band, by the human operator via `sudo` in their
own terminal (this repository's own ordinary pytest process runs as the
unprivileged configured-agent account, uid 501, and cannot write or, in
most cases, even read inside that directory). The literal results are
asserted below as recorded evidence; the full command transcript and
classification is in
`.pcae/evidence/PHASE_1R_1R_1R_PPA_REGISTRATION.json` and
`.pcae/evidence/PHASE_1R_1R_1R_PRIVILEGED_COMMAND_AUDIT.json`, and the
canonical Phase Report prose.

Strictly read-only against the real filesystem and git history outside
test-owned `tmp_path` fixtures. No protected-root mutation, no PPA
registration, no sudo invoked from within this test process, no
YubiKey, no FIDO2 PIN, no protected human APPROVE/REJECT.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core.hpac_foundation import canonical_digest  # noqa: E402
from pcae.core.phase_id import compare, parse, same_branch, same_series  # noqa: E402

# Phase-entry SHA (G0), frozen at the start of this phase's substantive work.
G0 = "4fa2ddb1fe1ef6b4b7588bbaa49131d11120efb5"

PREDECESSOR_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)
THIS_PHASE_ID = (
    "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R"
)

_EXPECTED_HELPER_SHA256 = "933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182"
_EXPECTED_HELPER_BYTE_LENGTH = 16295
_EXPECTED_VERIFIER_CONFIG_OBJECT = {"schema": "v1", "verifier_kind": "pcae-protected-local-presentation/1.0"}
_EXPECTED_VERIFIER_CONFIG_DIGEST = "951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85"

_REGISTRATION_EVIDENCE = REPO_ROOT / ".pcae/evidence/PHASE_1R_1R_1R_PPA_REGISTRATION.json"
_AUDIT_EVIDENCE = REPO_ROOT / ".pcae/evidence/PHASE_1R_1R_1R_PRIVILEGED_COMMAND_AUDIT.json"


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


# ═══════════════════════════════════════════════════════════════════════
# CPIPC SUCCESSOR VALIDITY
# ═══════════════════════════════════════════════════════════════════════


def test_this_phase_id_is_the_direct_cpipc_successor_of_the_predecessor():
    pred = parse(PREDECESSOR_PHASE_ID)
    cand = parse(THIS_PHASE_ID)
    assert same_series(pred, cand)
    assert same_branch(pred, cand)
    assert compare(pred, cand) == "less"
    assert cand.subphase[:-1] == pred.subphase
    assert cand.subphase[-1] == (1, "R")


def test_this_phase_id_is_not_reused_anywhere_in_history():
    result = _git("log", "--all", "--oneline", "--grep", THIS_PHASE_ID, "--format=%H")
    prior_shas = {line for line in result.stdout.splitlines() if line}
    # The task-open/implementation commits made THIS phase are the only
    # legitimate occurrences; there must be no occurrence predating G0.
    for sha in prior_shas:
        ancestry = _git("merge-base", "--is-ancestor", sha, G0)
        assert ancestry.returncode != 0, f"{sha} predates G0 and already names this phase id"


# ═══════════════════════════════════════════════════════════════════════
# INDEPENDENTLY RECOMPUTED DIGESTS (helper + verifier config)
# ═══════════════════════════════════════════════════════════════════════


def test_helper_source_sha256_independently_recomputed():
    data = (REPO_ROOT / "src/pcae/protected_presentation_helper.py").read_bytes()
    import hashlib

    assert len(data) == _EXPECTED_HELPER_BYTE_LENGTH
    assert hashlib.sha256(data).hexdigest() == _EXPECTED_HELPER_SHA256


def test_helper_source_unchanged_between_g0_and_head():
    diff = _git("diff", "--stat", G0, "HEAD", "--", "src/pcae/protected_presentation_helper.py")
    assert diff.stdout.strip() == ""


def test_verifier_configuration_digest_independently_recomputed():
    assert canonical_digest(_EXPECTED_VERIFIER_CONFIG_OBJECT) == _EXPECTED_VERIFIER_CONFIG_DIGEST


# ═══════════════════════════════════════════════════════════════════════
# REGISTRATION EVIDENCE SELF-CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════


def _load_evidence() -> dict:
    return json.loads(_REGISTRATION_EVIDENCE.read_text())


def test_registration_evidence_files_exist_and_parse():
    assert _REGISTRATION_EVIDENCE.is_file()
    assert _AUDIT_EVIDENCE.is_file()
    json.loads(_AUDIT_EVIDENCE.read_text())  # parses


def test_registration_evidence_phase_id_matches():
    evidence = _load_evidence()
    assert evidence["phase_id"] == THIS_PHASE_ID
    assert evidence["predecessor_phase_id"] == PREDECESSOR_PHASE_ID
    assert evidence["g0"] == G0


def _self_excluding_digest(document: dict, field: str) -> str:
    projected = dict(document)
    projected[field] = ""
    return canonical_digest(projected)


def test_installation_digest_recomputes_from_recorded_fields():
    evidence = _load_evidence()
    rec = evidence["post_registration_readback"]["installation_descriptor"]
    doc = {
        "installation_schema_version": rec["installation_schema_version"],
        "installation_id": rec["installation_id"],
        "mechanism_id": rec["mechanism_id"],
        "helper_implementation_id": rec["mechanism_id"],
        "helper_implementation_version": "pcae-protected-local-presentation-helper/1.0",
        "helper_path": rec["helper_path"],
        "helper_sha256": rec["helper_sha256"],
        "descriptor_digest": rec["descriptor_digest"],
        "verifier_configuration_digest": rec["verifier_configuration_digest"],
        "renderer_profile": rec["renderer_profile"],
        "generation": rec["generation"],
        "lifecycle_action": rec["lifecycle_action"],
        "status": rec["status"],
        "installed_at": "2026-09-05T16:53:22.143Z",
        "supersedes": None,
        "installation_digest": "",
    }
    assert _self_excluding_digest(doc, "installation_digest") == rec["installation_digest"]


def test_anchor_digest_recomputes_from_recorded_fields():
    evidence = _load_evidence()
    rec = evidence["post_registration_readback"]["current_generation_anchor"]
    doc = {
        "current_generation_schema_version": rec["current_generation_schema_version"],
        "installation_id": rec["installation_id"],
        "mechanism_id": "pcae-protected-local-presentation",
        "current_generation": rec["current_generation"],
        "installation_digest": rec["installation_digest"],
        "descriptor_digest": rec["descriptor_digest"],
        "status": rec["status"],
        "updated_at": "2026-09-05T16:53:22.143Z",
        "anchor_digest": "",
    }
    assert _self_excluding_digest(doc, "anchor_digest") == rec["anchor_digest"]


def test_installation_and_anchor_agree_on_installation_digest():
    evidence = _load_evidence()
    rb = evidence["post_registration_readback"]
    assert rb["installation_descriptor"]["installation_digest"] == rb["current_generation_anchor"]["installation_digest"]


def test_helper_sha256_matches_immutable_generation_1_source():
    evidence = _load_evidence()
    helper = evidence["post_registration_readback"]["helper_after_registration"]
    assert helper["sha256"] == _EXPECTED_HELPER_SHA256
    assert helper["unchanged_verified"] is True
    assert helper["matches_generation_1_immutable_source"] is True


def test_write_set_confined_to_authorized_ppa_paths():
    evidence = _load_evidence()
    rb = evidence["post_registration_readback"]
    actual = set(rb["write_set_actual"])
    expected_suffixes = {
        "presentation-mechanisms/v2/pcae-protected-local-presentation/descriptor.json",
        "presentation-mechanisms/v2/pcae-protected-local-presentation/current-generation.json",
        "presentation-mechanisms/v2/pcae-protected-local-presentation/installations/1/installation.json",
    }
    assert actual == expected_suffixes
    assert rb["write_set_confined"] is True


def test_protected_root_and_pawa_generation_preserved():
    evidence = _load_evidence()
    root_after = evidence["post_registration_readback"]["protected_root_after_registration"]
    pawa_after = evidence["post_registration_readback"]["pawa_anchor_after_registration"]
    assert root_after["owner_uid"] == 0
    assert root_after["mode_octal"] == "0700"
    assert root_after["configured_agent_uid_501_has_write_access_anywhere_in_chain"] is False
    assert root_after["root_anchor_generation_preserved"] == 1
    assert pawa_after["current_generation"] == 1
    assert pawa_after["unchanged_since_predecessor_phase"] is True


def test_final_verdicts_do_not_overclaim():
    evidence = _load_evidence()
    verdicts = evidence["final_verdicts"]
    assert verdicts["f5_protected_presentation_registration"] == "COMPLETE -- DEPLOYMENT-STATE IV PENDING"
    assert verdicts["f5"] == "DEPLOYED / IV PENDING"
    assert verdicts["n16_5"] == "NOT CLOSED"
    assert "VERIFIED" not in verdicts.get("f5", "")


# ═══════════════════════════════════════════════════════════════════════
# NO PRODUCT SOURCE / CONTRACT / DEPENDENCY CHANGE THIS PHASE
# ═══════════════════════════════════════════════════════════════════════


def test_no_production_source_change_since_g0():
    diff = _git("diff", "--name-only", G0, "HEAD", "--", "src/pcae", "scripts", "pyproject.toml")
    assert diff.stdout.strip() == ""


def test_no_contract_change_since_g0():
    diff = _git("diff", "--name-only", G0, "HEAD", "--", "docs/contracts")
    assert diff.stdout.strip() == ""


def test_no_test_weakening_in_this_phases_diff():
    """No existing `def test_` was renamed or removed in any touched test
    file across this phase's own diff (this new file is additive)."""
    import ast

    changed = _git("diff", "--name-only", G0, "HEAD", "--", "tests").stdout.split()
    for path in changed:
        if not path.endswith(".py"):
            continue
        old_show = _git("show", f"{G0}:{path}")
        old_defs: set[str] = set()
        if old_show.returncode == 0:
            old_tree = ast.parse(old_show.stdout)
            old_defs = {n.name for n in ast.walk(old_tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        new_text = (REPO_ROOT / path).read_text()
        new_tree = ast.parse(new_text)
        new_defs = {n.name for n in ast.walk(new_tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}
        assert old_defs <= new_defs, f"{path}: tests removed/renamed: {old_defs - new_defs}"


def test_runtime_state_unchanged():
    evidence = _load_evidence()
    runtime = evidence["runtime_final_check"]
    assert runtime["implementation"] == "not_implemented"
    assert runtime["state"] == "Observed"
    assert runtime["maximum_capability"] == "observe"
    assert runtime["execution_availability"] == "unavailable"
    assert runtime["plugins"] == 0
    assert runtime["capabilities"] == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
