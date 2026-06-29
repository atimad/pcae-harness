"""CLI runners for pcae backend commands — Phase 94E.

Dry-run/read-only only.  No backend invocation, no subprocess, no network.
"""
from __future__ import annotations

import argparse
import json

from pcae.core.backend_invocations import (
    get_default_registry,
    make_invocation_request,
    check_invocation_readiness,
    read_latest_prompt,
    read_latest_output,
    INVOCATION_MODE_DRY_RUN,
    APPROVAL_PENDING,
)


def run_backend_list(args: argparse.Namespace) -> int:
    """pcae backend list [--json]"""
    reg = get_default_registry()
    entries = []
    for bid, b in reg.items():
        entries.append({
            "backend_id": bid,
            "backend_type": b.backend_type,
            "risk_level": b.risk_level,
            "requires_human_approval": b.requires_human_approval,
            "supports_prompt_capture": b.supports_prompt_capture,
            "supports_output_capture": b.supports_output_capture,
            "supports_artifact_only_mode": b.supports_artifact_only_mode,
        })

    if args.json:
        print(json.dumps({"backends": entries}, indent=2))
    else:
        print(f"Backend registry — {len(entries)} backend(s)")
        for e in entries:
            approval = "yes" if e["requires_human_approval"] else "no"
            print(f"  {e['backend_id']:20s}  type={e['backend_type']:5s}  "
                  f"risk={e['risk_level']:8s}  approval={approval}")
        print()
        print("  ⚠️  No backend invocation capability. Read-only metadata.")
    return 0


def run_backend_status(args: argparse.Namespace) -> int:
    """pcae backend status [--json]"""
    from pathlib import Path
    reg = get_default_registry()
    artifact_dir = Path(".pcae/backend-invocations")
    has_prompt = (artifact_dir / "latest-prompt.md").exists()
    has_output = (artifact_dir / "latest-output.md").exists()
    latest_meta = read_latest_prompt()

    data = {
        "registry_available": True,
        "backend_count": len(reg),
        "artifact_directory": str(artifact_dir),
        "artifact_directory_exists": artifact_dir.exists(),
        "latest_prompt_present": has_prompt,
        "latest_output_present": has_output,
        "execution_capability": "none",
        "no_execution": True,
    }
    if latest_meta:
        data["latest_request_id"] = latest_meta.get("request_id", "")
        data["latest_backend_id"] = latest_meta.get("backend_id", "")

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("Backend invocation status")
        print(f"  Registry:              {data['backend_count']} backend(s)")
        print(f"  Artifact dir:          {'present' if artifact_dir.exists() else 'absent'}")
        print(f"  Latest prompt:         {'present' if has_prompt else 'absent'}")
        print(f"  Latest output:         {'present' if has_output else 'absent'}")
        if latest_meta:
            print(f"  Latest request:        {latest_meta.get('request_id', '')}")
            print(f"  Latest backend:        {latest_meta.get('backend_id', '')}")
        print(f"  Execution capability:  none")
        print()
        print("  ⚠️  Read-only status. No backend invocation capability.")
    return 0


def run_backend_plan(args: argparse.Namespace) -> int:
    """pcae backend plan --backend <id> [--request-id <id>] [--phase-id <id>] [--json]

    Dry-run only.  Creates a request, checks readiness.  Never invokes backend.
    """
    backend_id: str = getattr(args, "backend", "") or ""
    request_id: str = getattr(args, "request_id", "") or ""
    phase_id: str = getattr(args, "phase_id", "") or ""

    if not backend_id:
        msg = "Missing --backend <id>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    reg = get_default_registry()
    if backend_id not in reg:
        msg = f"Unknown backend: {backend_id!r}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    try:
        kwargs = {"backend_id": backend_id, "phase_id": phase_id}
        if request_id:
            kwargs["request_id"] = request_id
        req = make_invocation_request(**kwargs)
    except ValueError as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    readiness = check_invocation_readiness(req, reg)
    backend = reg[backend_id]

    if args.json:
        print(json.dumps({
            "request": req.to_dict(),
            "backend": backend.to_dict(),
            "readiness": readiness,
        }, indent=2))
    else:
        print("Backend invocation plan (dry-run)")
        print(f"  Backend:         {backend_id}")
        print(f"  Request ID:      {req.request_id}")
        print(f"  Phase ID:        {phase_id or '(none)'}")
        print(f"  Risk level:      {backend.risk_level}")
        print(f"  Needs approval:  {'yes' if backend.requires_human_approval else 'no'}")
        print(f"  Execution mode:  {req.execution_mode}")
        print(f"  No execution:    {req.no_execution_by_default}")
        print()
        print(f"  Readiness:       {readiness['status']}")
        if readiness.get("missing_evidence"):
            print(f"  Missing:         {', '.join(readiness['missing_evidence'])}")
        if readiness.get("hard_blocks"):
            print(f"  Hard blocks:     {', '.join(readiness['hard_blocks'])}")
        if readiness.get("warnings"):
            print(f"  Warnings:        {', '.join(readiness['warnings'])}")
        print()
        print("  ⚠️  Dry-run only. No backend was invoked.")

    return 0 if readiness["status"] != "blocked" else 1


def run_backend_show(args: argparse.Namespace) -> int:
    """pcae backend show --latest [--json]"""
    meta = read_latest_prompt()
    output_meta = read_latest_output()

    if not meta and not output_meta:
        msg = "No invocation artifacts found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps({
            "latest_invocation": meta,
            "latest_output": output_meta,
        }, indent=2))
    else:
        print("Backend invocation — latest artifact")
        if meta:
            print(f"  Request ID:      {meta.get('request_id', '')}")
            print(f"  Backend ID:      {meta.get('backend_id', '')}")
            print(f"  Phase ID:        {meta.get('phase_id', '')}")
            print(f"  Prompt hash:     {(meta.get('prompt_hash', '') or '')[:16]}...")
            print(f"  Prompt path:     {meta.get('prompt_artifact_path', '')}")
            ra = meta.get('redaction_applied', False)
            print(f"  Redaction:       {'applied' if ra else 'none'}")
        if output_meta:
            print(f"  Output hash:     {(output_meta.get('output_hash', '') or '')[:16]}...")
            print(f"  Output path:     {output_meta.get('output_artifact_path', '')}")
            print(f"  Quarantined:     {output_meta.get('quarantined', True)}")
            print(f"  Applied:         {output_meta.get('applied_to_repo', False)}")
        print()
        print("  ⚠️  Metadata only — no raw prompt/output printed.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94G — Backend audit subcommands
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_audit_show(args: argparse.Namespace) -> int:
    """pcae backend audit show --latest [--json]"""
    from pcae.core.backend_invocations import read_latest_backend_audit
    record = read_latest_backend_audit()
    if not record:
        msg = "No backend audit records found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print("Backend audit — latest")
        print(f"  Audit ID:      {record.get('audit_id', '')}")
        print(f"  Event:         {record.get('event_type', '')}")
        print(f"  Backend:       {record.get('backend_id', '')}")
        print(f"  Readiness:     {record.get('readiness_status', '')}")
        print(f"  Timestamp:     {record.get('timestamp_utc', '')}")
        print(f"  Digest:        {(record.get('record_digest', '') or '')[:16]}...")
    return 0


def run_backend_audit_list(args: argparse.Namespace) -> int:
    """pcae backend audit list [--limit N] [--json]"""
    from pcae.core.backend_invocations import list_backend_audit
    limit = int(getattr(args, "limit", 10) or 10)
    records = list_backend_audit(limit=limit)
    if args.json:
        print(json.dumps(records, indent=2))
    else:
        if not records:
            print("No backend audit records found.")
        else:
            print(f"Backend audit — last {len(records)} record(s)")
            for r in records:
                print(f"  {r['file']}  {r['event_type']:20s}  {r['backend_id']:10s}  {r['readiness_status']}")
    return 0


def run_backend_audit_verify(args: argparse.Namespace) -> int:
    """pcae backend audit verify [--json]"""
    from pcae.core.backend_invocations import verify_backend_audit
    result = verify_backend_audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Backend audit verify")
        print(f"  Total:    {result['total']}")
        print(f"  Valid:    {result['valid']}")
        print(f"  Tampered: {result['tampered']}")
        if result["tampered"] > 0:
            print(f"  ⚠️  {result['tampered']} tampered record(s)!")
        else:
            print(f"  ✅  All records intact.")
    return 0 if result["tampered"] == 0 else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94H — Trust/readiness gate CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_readiness(args: argparse.Namespace) -> int:
    """pcae backend readiness --latest [--json]"""
    from pcae.core.backend_invocations import (
        assess_backend_invocation_trust, read_latest_prompt,
        read_latest_output, read_latest_backend_audit, verify_backend_audit,
    )
    prompt_meta = read_latest_prompt()
    output_meta = read_latest_output()
    audit_meta = read_latest_backend_audit()
    audit_ok = verify_backend_audit().get("tampered", 1) == 0

    assessment = assess_backend_invocation_trust(
        prompt_meta=prompt_meta, output_meta=output_meta,
        audit_meta=audit_meta, audit_verified=audit_ok,
    )

    if args.json:
        print(json.dumps(assessment, indent=2))
    else:
        print("Backend invocation trust/readiness assessment")
        print(f"  Status:           {assessment['status']}")
        print(f"  Trust level:      {assessment['trust_level']}")
        print(f"  Invocation ready: {assessment['backend_invocation_ready']}")
        print()
        print(f"  Prompt artifact:  {'present' if assessment['checks'].get('prompt_artifact_present') else 'missing'}")
        print(f"  Output artifact:  {'present' if assessment['checks'].get('output_artifact_present') else 'missing'}")
        print(f"  Audit record:     {'present' if assessment['checks'].get('audit_record_present') else 'missing'}")
        print(f"  Output quarantined: {assessment['checks'].get('output_quarantined', True)}")
        print(f"  Applied to repo:  {assessment['checks'].get('applied_to_repo', False)}")
        if assessment["hard_blocks"]:
            print(f"  Hard blocks:      {', '.join(assessment['hard_blocks'])}")
        if assessment["missing_evidence"]:
            print(f"  Missing:          {', '.join(assessment['missing_evidence'])}")
        if assessment["warnings"]:
            print(f"  Warnings:         {', '.join(assessment['warnings'])}")
        print()
        print(f"  Recommended:      {assessment['recommended_action']}")
        print(f"  No real backend:  True")
        print(f"  No subprocess:    True")
        print(f"  No network:       True")
    return 0 if not assessment["hard_blocks"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94L — Apply readiness CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_apply_readiness_show(args: argparse.Namespace) -> int:
    """pcae backend apply-readiness show --latest [--json]

    Read-only display of latest apply readiness assessment.
    Never executes apply, never mutates files.
    """
    from pcae.core.backend_invocations import read_latest_apply_readiness

    assessment = read_latest_apply_readiness()
    if assessment is None:
        msg = "No apply readiness assessments found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        print("Apply readiness — latest assessment")
        print(f"  Assessment ID:     {assessment.assessment_id}")
        print(f"  Apply plan ID:     {assessment.apply_plan_id}")
        print(f"  Review ID:         {assessment.review_id}")
        print(f"  Approval ID:       {assessment.approval_id}")
        print(f"  Request ID:        {assessment.request_id}")
        print(f"  Phase ID:          {assessment.phase_id}")
        print(f"  Task ID:           {assessment.task_id}")
        print(f"  Backend ID:        {assessment.backend_id}")
        print(f"  Status:            {assessment.status}")
        print(f"  Apply ready:       {assessment.apply_ready}")
        print(f"  Trust level:       {assessment.trust_level}")
        print()
        print(f"  Output hash OK:    {assessment.output_hash_verified}")
        print(f"  Approval bound:    {assessment.approval_bound_to_output_hash}")
        print(f"  Review valid:      {assessment.review_state_valid}")
        print(f"  Output quarantined:{assessment.output_quarantined}")
        print(f"  Output not applied:{assessment.output_not_applied}")
        print(f"  Allowed files ok:  {assessment.allowed_files_present}")
        print(f"  Forbidden present: {assessment.forbidden_files_present}")
        print(f"  Operations valid:  {assessment.operations_valid}")
        print(f"  Rollback ready:    {assessment.rollback_ready}")
        print(f"  Tests defined:     {assessment.tests_defined}")
        print(f"  Check required:    {assessment.check_required}")
        if assessment.hard_blocks:
            print(f"  Hard blocks:       {', '.join(assessment.hard_blocks)}")
        if assessment.missing_evidence:
            print(f"  Missing evidence:  {', '.join(assessment.missing_evidence)}")
        if assessment.warnings:
            print(f"  Warnings:          {', '.join(assessment.warnings)}")
        print()
        print(f"  Recommended action: {assessment.recommended_action}")
        print(f"  Schema version:     {assessment.schema_version}")
        print()
        print("  ⚠️  Read-only. Apply readiness is not apply execution.")
    return 0


def run_backend_apply_readiness_validate(args: argparse.Namespace) -> int:
    """pcae backend apply-readiness validate --plan <path> [--json]

    Reads an apply plan JSON, validates readiness, persists and displays
    the assessment.  Never executes apply, never mutates files.
    """
    import json as _json
    from pathlib import Path as _Path
    from pcae.core.backend_invocations import (
        ApplyPlan, ReviewArtifact, ApprovalArtifact,
        validate_backend_apply_readiness, persist_apply_readiness,
    )

    plan_path: str = getattr(args, "plan", "") or ""
    review_path: str | None = getattr(args, "review", None) or None
    approval_path: str | None = getattr(args, "approval", None) or None
    output_path: str | None = getattr(args, "output", None) or None
    trust_path: str | None = getattr(args, "trust", None) or None

    if not plan_path:
        msg = "Missing --plan <path>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    p = _Path(plan_path)
    if not p.is_file():
        msg = f"Apply plan not found: {plan_path}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    try:
        plan_data = _json.loads(p.read_text())
        plan = ApplyPlan(**{k: v for k, v in plan_data.items()
                             if k in ApplyPlan.__dataclass_fields__})
    except Exception as exc:
        msg = f"Failed to load apply plan: {exc}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    review: ReviewArtifact | None = None
    if review_path:
        rp = _Path(review_path)
        if not rp.is_file():
            msg = f"Review artifact not found: {review_path}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            rd = _json.loads(rp.read_text())
            review = ReviewArtifact(**{k: v for k, v in rd.items()
                                        if k in ReviewArtifact.__dataclass_fields__})
        except Exception as exc:
            msg = f"Failed to load review: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1

    approval: ApprovalArtifact | None = None
    if approval_path:
        ap = _Path(approval_path)
        if not ap.is_file():
            msg = f"Approval artifact not found: {approval_path}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            ad = _json.loads(ap.read_text())
            approval = ApprovalArtifact(**{k: v for k, v in ad.items()
                                            if k in ApprovalArtifact.__dataclass_fields__})
        except Exception as exc:
            msg = f"Failed to load approval: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1

    output_meta: dict | None = None
    if output_path:
        op = _Path(output_path)
        if op.is_file():
            try:
                output_meta = _json.loads(op.read_text())
            except Exception:
                pass

    trust_assessment: dict | None = None
    if trust_path:
        tp = _Path(trust_path)
        if tp.is_file():
            try:
                trust_assessment = _json.loads(tp.read_text())
            except Exception:
                pass

    assessment = validate_backend_apply_readiness(
        plan=plan, review=review, approval=approval,
        output_meta=output_meta, trust_assessment=trust_assessment,
    )
    persist_result = persist_apply_readiness(assessment)

    if args.json:
        print(json.dumps({
            "assessment": assessment.to_dict(),
            "persistence": persist_result,
        }, indent=2))
    else:
        print("Apply readiness validation")
        print(f"  Assessment ID:     {assessment.assessment_id}")
        print(f"  Status:            {assessment.status}")
        print(f"  Apply ready:       {assessment.apply_ready}")
        print(f"  Trust level:       {assessment.trust_level}")
        if assessment.hard_blocks:
            print(f"  Hard blocks:       {', '.join(assessment.hard_blocks)}")
        if assessment.missing_evidence:
            print(f"  Missing evidence:  {', '.join(assessment.missing_evidence)}")
        if assessment.warnings:
            print(f"  Warnings:          {', '.join(assessment.warnings)}")
        print()
        print(f"  Recommended action: {assessment.recommended_action}")
        if persist_result.get("status") == "written":
            print(f"  Persisted to:       {persist_result.get('path', 'unknown')}")
        else:
            print(f"  Persistence:        {persist_result.get('status', 'unknown')}")
        print()
        print("  ⚠️  Read-only validation. No apply execution, no file mutation.")

    return 0 if assessment.apply_ready else 1
