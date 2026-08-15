"""HATP Class-B Deployment Conformance Aggregator — Phase 149O.20I,
Wave D/E (bounded, non-authoritative implementation).

Combines `hatp_class_b_topology_verifier.verify_class_b_topology_
conformance()` and `hatp_environment_lock_verifier.verify_environment_
lock_conformance()` with the Model-A / deployment-identity checks
(HBDC-REQ-022, HBDC-REQ-024, HBDC-REQ-042..046) designed in
`docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_
LOCK_IMPLEMENTATION_PLAN.md` §15, into a single
`ClassBDeploymentVerificationResult`.

**Non-authoritative by design (CBV-S1, plan §24/§54/§58).** This is the
single production entry point that would eventually feed a future
readiness/certification/activation path. As of Phase 149O.20I, none of
the three 149O.20I modules is a member of HMIC-001's current 25-file
frozen identity — `verify_class_b_deployment_conformance()`'s result
MUST NOT be consumed by `hatp_mandatory_cutover.py` or any other
authority-bearing production code path until a future, separately-
governed phase evolves HMIC's source scope to include these three
modules and that evolution is independently verified (plan §24 Wave
F). This module has no way to answer "am I HMIC-bound?" about itself
and does not attempt to (plan §25 — no self-certification): enforcement
of that restriction lives entirely in caller discipline, not here.

`ClassBConformanceStatus.COMPLIANT` from this aggregator is strictly
narrower than HMIC `VALID`, overall HATP readiness, `HATP_MANDATORY`
activation, Permission Broker `ALLOW`, or rollback-execution readiness
(HBDC-REQ-055, plan §21). It does not claim runtime executed-source
cryptographic attestation (HBDC-REQ-041). A successful result does not
itself authorize real Protected Root creation, real OS principal
provisioning, real HMIC certification, real active binding, real
Cutover Record transition, or real `HATP_MANDATORY` activation
(HBDC-REQ-050/051) — each requires its own separately authorized
governed phase.

**Strictly read-only.** No mutation of any kind.
"""
from __future__ import annotations

import importlib.metadata
from pathlib import Path
from typing import Optional

from pcae.core import hatp_bootstrap
from pcae.core import repository_identity
from pcae.core.hatp_class_b_topology_verifier import (
    ClassBCheckResult,
    ClassBConformanceStatus,
    ClassBDeploymentVerificationResult,
    _build_result,
    _safe_check,
)
from pcae.core.hatp_class_b_topology_verifier import verify_class_b_topology_conformance
from pcae.core.hatp_environment_lock_verifier import verify_environment_lock_conformance
from pcae.core.paths import HarnessPath

__all__ = [
    "ClassBCheckResult",
    "ClassBConformanceStatus",
    "ClassBDeploymentVerificationResult",
    "verify_class_b_deployment_conformance",
]


def _check_model_a_deployment(agent_uid: int) -> ClassBCheckResult:
    """HBDC-REQ-022/024: Model A is the only authorized deployment
    model under HBDC-001 v1.0. Detected via the `pcae` distribution's
    editable-install flag (`direct_url.json`'s `editable` key, PEP 660)
    — not assumed."""

    try:
        dist = importlib.metadata.distribution("pcae-harness")
    except importlib.metadata.PackageNotFoundError:
        return ClassBCheckResult("HBDC-REQ-022", False, "pcae_distribution_metadata_not_found", ())
    direct_url_text: Optional[str]
    try:
        direct_url_text = dist.read_text("direct_url.json")
    except Exception:  # noqa: BLE001 - fail closed on any metadata-read failure
        direct_url_text = None
    if direct_url_text is None:
        return ClassBCheckResult(
            "HBDC-REQ-022", False, "no_direct_url_metadata_model_a_editable_install_unconfirmed", ()
        )
    import json as _json

    try:
        payload = _json.loads(direct_url_text)
    except ValueError:
        return ClassBCheckResult("HBDC-REQ-022", False, "direct_url_metadata_malformed", ())
    is_editable = bool(payload.get("dir_info", {}).get("editable", False))
    if not is_editable:
        return ClassBCheckResult("HBDC-REQ-024", False, "unsupported_deployment_model_not_editable_install", ())
    return ClassBCheckResult("HBDC-REQ-022", True, "model_a_editable_install_confirmed", (str(dist._path),))


def _check_deployment_identity(root: HarnessPath) -> ClassBCheckResult:
    """HBDC-REQ-042..046: thin wrapper over the existing, unmodified
    `resolve_canonical_deployment_root` / `read_repository_identity` /
    `deployment_binding_matches` — this check reimplements none of
    their semantics (plan §15). On a host with no provisioned
    `DeploymentBinding` (the expected current state, per phase entry
    baseline), this reports `NON_COMPLIANT`, never `COMPLIANT` by
    default."""

    try:
        canonical_root = hatp_bootstrap.resolve_canonical_deployment_root(root.path)
    except OSError as exc:
        return ClassBCheckResult("HBDC-REQ-042", False, "canonical_deployment_root_unresolvable", (repr(exc),))

    try:
        identity = repository_identity.read_repository_identity(root)
    except repository_identity.RepositoryIdentityMalformedError as exc:
        return ClassBCheckResult("HBDC-REQ-042", False, "repository_identity_malformed", (repr(exc),))
    if identity is None:
        return ClassBCheckResult("HBDC-REQ-042", False, "no_repository_identity_present", (canonical_root,))

    try:
        store = hatp_bootstrap.HATPTrustStore.production()
        binding = store.load_repository_enrollment(identity.repository_instance_id)
    except hatp_bootstrap.HATPTrustStoreError as exc:
        return ClassBCheckResult("HBDC-REQ-042", False, "trust_store_unavailable", (repr(exc),))

    matches = hatp_bootstrap.deployment_binding_matches(
        binding,
        repository_id=identity.repository_instance_id,
        canonical_deployment_root=canonical_root,
    )
    if not matches:
        return ClassBCheckResult(
            "HBDC-REQ-042", False, "no_active_deployment_binding_matches_repository_and_root", (canonical_root,)
        )
    return ClassBCheckResult("HBDC-REQ-042", True, "deployment_binding_matches_repository_and_root", (canonical_root,))


def verify_class_b_deployment_conformance(
    root: Optional[HarnessPath] = None,
) -> ClassBDeploymentVerificationResult:
    """DIAGNOSTIC ONLY — NOT AN AUTHORITATIVE READINESS SIGNAL.

    Aggregates topology conformance, environment-lock conformance,
    Model-A deployment detection, and deployment-identity binding into
    a single `ClassBDeploymentVerificationResult` (HBDC-REQ-052/053:
    only exact all-satisfied yields `COMPLIANT`; any failure, missing
    evidence, or indeterminate check prevents it — no partial credit).
    Accepts only a neutral repository-root locator, defaulting to the
    current working directory — never an authority boolean.
    """

    if root is None:
        root = HarnessPath.cwd()

    topology = verify_class_b_topology_conformance()
    environment = verify_environment_lock_conformance()

    from pcae.core.hatp_environment_lock_verifier import _current_agent_identity

    agent_uid, _agent_gids = _current_agent_identity()

    checks: "list[ClassBCheckResult]" = list(topology.checks) + list(environment.checks)
    checks.append(_safe_check("HBDC-REQ-022", lambda: _check_model_a_deployment(agent_uid)))
    checks.append(_safe_check("HBDC-REQ-042", lambda: _check_deployment_identity(root)))

    return _build_result(checks)
