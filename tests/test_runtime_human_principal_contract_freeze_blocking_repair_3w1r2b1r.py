"""Static STOP-gate verification for Phase 149O.20L.7O.3W.1R.2B.1R.

This suite proves the nine-finding inventory and the B-6 scope collision
without executing an authenticator or importing production runtime code.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "docs/PHASE_149O_20L_7O_3W_1R_2B_1_INDEPENDENT_VERIFICATION_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE.md"
HPAC = ROOT / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RIHAC = ROOT / "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md"
RIASC = ROOT / "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md"
PBRD = ROOT / "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md"
RDGO = ROOT / "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md"
RPAC = ROOT / "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md"
TASK = ROOT / "tasks/done/20260827-2147-phase-149o-20l-7o-3w-1r-2b-1r-runtime-invocation-human-principal-authentication-contract-freeze-blocking-repair.md"


BLOCKING = (
    "B-1 — Principal registry/bootstrap/configuration trust root is not same-user-agent resistant. Location and “non-agent-invocable” convention do not replace protected ownership/ACL/separate-principal enforcement.",
    "B-2 — UP-only overclaims a named authenticated human. UV is optional and no exclusive credential custody is frozen.",
    "B-3 — Blind touch can substitute for informed approval. No non-forgeable confirmation evidence or trusted subject display is bound.",
    "B-4 — Proof schema/store/reference contract is incomplete and internally inconsistent. Canonical resolution cannot be implemented uniquely.",
    "B-5 — Revocation does not invalidate an outstanding gate-5-validated, unconsumed approval. Current-principal assurance can go stale before dispatch.",
    "B-6 — PBRD/RDGO still normatively pin RIHAC/RIASC v1.0. The active contract graph is ambiguous and permits the insecure predecessor.",
    "B-7 — Proof nonce consumption at gate 5 contradicts mandatory pre-gate-9 approval revalidation. The frozen lifecycle is not implementable consistently.",
)

MUST_FIX = (
    "M-1 — RIHAC v1.1 should be a new MAJOR. The change is mandatory and semantically incompatible, not optional evidence or mere clarification.",
    "M-2 — Internal cross-references are stale/mistargeted. Examples: HPAC references nonexistent §39–§41 and mispoints fallback sections; RIHAC calls software fallback HPAC §15 although §15 is domain separation.",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(value: str) -> str:
    return " ".join(value.replace("**", "").split())


def test_primary_artifact_contains_exactly_seven_blocking_findings() -> None:
    section = text(VERIFY).split("### BLOCKING", 1)[1].split("### MUST-FIX", 1)[0]
    rows = re.findall(r"^\d+\. \*\*(B-[1-7].*?)(?=^\d+\. |\Z)", section, re.M | re.S)
    assert tuple(normalized(row) for row in rows) == BLOCKING


def test_primary_artifact_contains_exactly_two_must_fix_findings() -> None:
    section = text(VERIFY).split("### MUST-FIX", 1)[1].split("### NON-BLOCKING", 1)[0]
    rows = re.findall(r"^\d+\. \*\*(M-[1-2].*?)(?=^\d+\. |\Z)", section, re.M | re.S)
    assert tuple(normalized(row) for row in rows) == MUST_FIX


def test_contract_identities_match_failed_freeze() -> None:
    assert "**Version:** 1.0" in text(HPAC)
    assert "**Version:** 1.1" in text(RIHAC)
    assert "**Version:** 2.0" in text(RIASC)


def test_failed_freeze_contract_bytes_remain_unchanged() -> None:
    expected = {
        HPAC: "7a2792f4a825f4d3c90425f43f557babc8f991c9a4f4efe5970601a7ae09bc1b",
        RIHAC: "35365049fd4dd7a4b381f93173c56711a9b540915f06c3ebbb47dcd3e950cc91",
        RIASC: "af7ba866befab405a7f10b0e8bfceac5e573e9ef0580fe8bb9552e527301b760",
    }
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in expected} == expected


def test_b1_registry_root_is_only_same_user_convention() -> None:
    hpac = text(HPAC)
    assert "outside any single\n  repository" in hpac
    assert "non-agent-invocable admin tool" in hpac
    assert "separate OS" not in hpac[hpac.index("## 7."):hpac.index("## 8.")]


def test_b2_up_only_overclaims_named_identity() -> None:
    hpac = text(HPAC)
    flat = normalized(hpac)
    assert "UP alone is therefore the v1 minimum" in flat
    assert "UV optional, deployment-configurable" in flat
    assert "exclusive custody" not in flat


def test_b3_no_verifiable_trusted_presentation() -> None:
    joined = text(HPAC) + text(RIHAC) + text(RIASC)
    assert "interactive_local_cli_confirmation" in joined
    assert "confirmation_proof_ref" not in joined
    assert "trusted display" not in joined.lower()


def test_b4_proof_schema_and_reference_are_inconsistent() -> None:
    hpac, rihac, riasc = text(HPAC), text(RIHAC), text(RIASC)
    assert "SHALL contain exactly:" in hpac and "proof_id" in hpac
    assert '"required": ["artifact_id", "artifact_digest"]' in riasc
    assert "(`proof_id`, `proof_digest`)" in riasc
    assert "`challenge_subject`" in rihac
    assert "`challenge_subject`" not in hpac


def test_b5_revocation_preserves_unconsumed_validated_approval() -> None:
    assert "does not retroactively invalidate a `RuntimeInvocationApproval`\n  already validated" in text(HPAC)
    assert "already validated at gate 5" in normalized(text(RIHAC))


def test_b6_requires_out_of_scope_pbrd_and_rdgo_edits() -> None:
    assert "RIHAC-001 v1.0" in text(PBRD).split("## 0.", 1)[0]
    rdgo_header = text(RDGO).split("## 0.", 1)[0]
    assert "RIHAC-001 v1.0" in rdgo_header
    assert "RIASC-001 v1.0" in rdgo_header
    task = text(TASK)
    assert "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md" not in task
    assert "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md" not in task


def test_b7_gate5_consumption_conflicts_with_revalidation() -> None:
    hpac, rihac, rdgo = text(HPAC), text(RIHAC), text(RDGO)
    assert "recorded as consumed at the moment\n  verification succeeds" in hpac
    assert "complete\n  validation" in rihac and "run\n  again successfully" in rihac
    assert "full revalidation" in rdgo


def test_m1_rihac_semantics_are_major_incompatible() -> None:
    rihac = text(RIHAC)
    assert 'v1.0 sentence "No cryptographic signature is\nrequired for v1" is retired' in rihac
    assert "semantic redefinition" in rihac
    assert "**Version:** 1.1" in rihac


def test_m2_stale_cross_references_reproduce() -> None:
    hpac, rihac = text(HPAC), text(RIHAC)
    assert "§39-§41 below" in hpac
    assert "gated software-key fallback (HPAC-001 §15)" in rihac
    assert "## 15. Domain separation" in hpac
    assert "## 38. Freeze verdict" in hpac


def test_rpac_needs_no_change_for_scope_stop() -> None:
    rpac = text(RPAC)
    assert "**Version:** 1.0" in rpac
    assert "HATP is not a generic adapter-contract prerequisite" in rpac


def test_scope_gate_requires_stop_before_any_contract_edit() -> None:
    verification = normalized(text(VERIFY))
    assert "PBRD's normative header still pins RIHAC-001 v1.0" in verification
    assert "RDGO's normative header still pins RIHAC-001 v1.0 and RIASC-001 v1.0" in verification
    assert all(path.stat().st_size > 0 for path in (HPAC, RIHAC, RIASC, PBRD, RDGO, RPAC))
