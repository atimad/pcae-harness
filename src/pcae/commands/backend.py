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
    run_mock_lifecycle_demo,
    persist_lifecycle_demo,
    read_latest_lifecycle_demo,
    get_default_adapter_registry,
    validate_backend_adapter_preflight,
    BackendAdapterPreflightArtifact,
    persist_backend_adapter_preflight_artifact,
    verify_backend_adapter_preflight_artifact,
    load_latest_backend_adapter_preflight_artifact,
    load_latest_real_adapter_invocation_approval,
    verify_real_adapter_invocation_approval,
    create_real_adapter_invocation_plan,
    load_latest_real_adapter_invocation_plan,
    verify_real_adapter_invocation_plan,
    persist_real_adapter_invocation_plan,
    evaluate_artifact_only_real_invocation_dry_run,
    ArtifactOnlyRealInvocationDryRunAssessment,
    RealAdapterInvocationPlan,
    load_latest_claude_runtime_evidence,
    verify_claude_runtime_evidence,
    import_claude_runtime_evidence_from_json,
    persist_claude_runtime_evidence,
    detect_claude_runtime_evidence_stat_only,
    ClaudeRuntimeDetectionConfig,
    ClaudeRuntimeEvidence,
    persist_artifact_only_real_invocation_dry_run_assessment,
    load_latest_artifact_only_real_invocation_dry_run_assessment,
    verify_artifact_only_real_invocation_dry_run_assessment,
    BackendAdapterContract,
    INVOCATION_MODE_DRY_RUN,
    APPROVAL_PENDING,
    DEMO_COMPLETED,
    DEMO_BLOCKED,
    DEMO_PARTIAL,
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
# Phase 94M — Backend review CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_review_show(args: argparse.Namespace) -> int:
    """pcae backend review show --latest [--json]

    Display latest review artifact metadata only.
    Never prints raw prompt/output content.
    """
    from pcae.core.backend_invocations import read_latest_review

    review = read_latest_review()
    if review is None:
        msg = "No review artifacts found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(review.to_dict(), indent=2))
    else:
        print("Backend review — latest artifact")
        print(f"  Review ID:         {review.review_id}")
        print(f"  Request ID:        {review.request_id}")
        print(f"  Phase ID:          {review.phase_id}")
        print(f"  Backend ID:        {review.backend_id}")
        print(f"  Review state:      {review.review_state}")
        print(f"  Output hash:       {(review.output_hash or '')[:16]}...")
        print(f"  Approved:          {review.approved_for_apply}")
        print(f"  Rejected:          {review.rejected}")
        print(f"  Apply ready:       {review.apply_ready}")
        print(f"  Operator:          {review.operator or '(none)'}")
        print(f"  Decision:          {review.decision or '(none)'}")
        if review.hard_blocks:
            print(f"  Hard blocks:       {', '.join(review.hard_blocks)}")
        if review.missing_evidence:
            print(f"  Missing evidence:  {', '.join(review.missing_evidence)}")
        if review.warnings:
            print(f"  Warnings:          {', '.join(review.warnings)}")
        print(f"  Created at:        {review.created_at_utc}")
        print()
        print("  ⚠️  Metadata only — no raw prompt/output content printed.")
    return 0


def run_backend_review_create(args: argparse.Namespace) -> int:
    """pcae backend review create --request-id <id> --output-hash <hash> [--json]

    Create a review artifact in review_pending state with safe defaults.
    Persists under .pcae/backend-reviews/. Never applies anything.
    """
    from pcae.core.backend_invocations import (
        create_review_artifact, persist_review, REVIEW_PENDING,
    )

    request_id: str = getattr(args, "request_id", "") or ""
    output_hash: str = getattr(args, "output_hash", "") or ""
    phase_id: str = getattr(args, "phase_id", "") or ""
    backend_id: str = getattr(args, "backend", "") or ""
    output_artifact_path: str = getattr(args, "output_artifact_path", "") or ""
    prompt_hash: str = getattr(args, "prompt_hash", "") or ""
    prompt_artifact_path: str = getattr(args, "prompt_artifact_path", "") or ""

    if not request_id:
        msg = "Missing --request-id"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not output_hash:
        msg = "Missing --output-hash"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    try:
        review = create_review_artifact(
            request_id=request_id,
            output_hash=output_hash,
            backend_id=backend_id,
            phase_id=phase_id,
            output_artifact_path=output_artifact_path,
            prompt_hash=prompt_hash,
            prompt_artifact_path=prompt_artifact_path,
        )
        review.review_state = REVIEW_PENDING
    except ValueError as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    result = persist_review(review)
    if result.get("status") != "written":
        msg = f"Failed to persist review: {result.get('error', 'unknown')}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps({
            "review": review.to_dict(),
            "persistence": result,
            "no_execution": True,
            "no_apply": True,
        }, indent=2))
    else:
        print("Backend review created")
        print(f"  Review ID:     {review.review_id}")
        print(f"  Request ID:    {review.request_id}")
        print(f"  Output hash:   {(review.output_hash or '')[:16]}...")
        print(f"  Review state:  {review.review_state}")
        print(f"  Approved:      {review.approved_for_apply}")
        print(f"  Rejected:      {review.rejected}")
        print(f"  Apply ready:   {review.apply_ready}")
        print(f"  Artifact:      {result.get('path', '')}")
        print()
        print("  ⚠️  Review created. No apply execution, no file mutation.")
    return 0


def run_backend_review_approve(args: argparse.Namespace) -> int:
    """pcae backend review approve --review-id <id> --output-hash <hash>
        --operator <name> --reason <text> [--json]

    Create approval artifact bound to exact review_id and output_hash.
    Hard blocks prevent effective approval. Approval does not execute apply.
    Output remains quarantined. Never authorizes commit/push.
    """
    from pcae.core.backend_invocations import (
        read_latest_review, approve_review, persist_review, persist_approval,
    )

    review_id: str = getattr(args, "review_id", "") or ""
    output_hash: str = getattr(args, "output_hash", "") or ""
    operator: str = getattr(args, "operator", "") or ""
    reason: str = getattr(args, "reason", "") or ""

    if not review_id:
        msg = "Missing --review-id"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not output_hash:
        msg = "Missing --output-hash"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not operator:
        msg = "Missing --operator"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not reason:
        msg = "Missing --reason"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    review = read_latest_review()
    if review is None:
        msg = "No review artifact found. Create one with: pcae backend review create"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    # Verify review_id binding
    if review.review_id != review_id:
        msg = f"Review ID mismatch: found {review.review_id!r}, expected {review_id!r}"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    # Verify output_hash binding — hard block on mismatch
    if review.output_hash != output_hash:
        msg = f"Output hash mismatch — approval must bind to exact output hash"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    # Hard blocks prevent effective approval
    if review.hard_blocks:
        msg = f"Cannot approve: hard blocks present: {', '.join(review.hard_blocks)}"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    # Conflict: cannot approve a rejected review
    if review.rejected:
        msg = "Cannot approve: review is already rejected"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    try:
        approval = approve_review(review, operator, reason)
    except ValueError as exc:
        msg = str(exc)
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    persist_result = persist_approval(approval, review)
    if persist_result.get("status") != "written":
        msg = f"Failed to persist approval: {persist_result.get('error', 'unknown')}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps({
            "approval": approval.to_dict(),
            "review": review.to_dict(),
            "persistence": persist_result,
            "no_execution": True,
            "no_apply": True,
            "no_commit_push_authorization": True,
            "output_remains_quarantined": True,
        }, indent=2))
    else:
        print("Backend review approved")
        print(f"  Approval ID:   {approval.approval_id}")
        print(f"  Review ID:     {approval.review_id}")
        print(f"  Output hash:   {(approval.output_hash or '')[:16]}...")
        print(f"  Operator:      {approval.operator}")
        print(f"  Review state:  {review.review_state}")
        print(f"  Approved at:   {approval.approved_at_utc}")
        print(f"  Artifact:      {persist_result.get('approval_path', '')}")
        print()
        print("  ✅ Approval recorded. Output remains quarantined.")
        print("  ⚠️  Approval does not execute apply, authorize commit/push, or mutate files.")
    return 0


def run_backend_review_reject(args: argparse.Namespace) -> int:
    """pcae backend review reject --review-id <id> --output-hash <hash>
        --operator <name> --reason <text> [--json]

    Create rejection artifact bound to exact review_id and output_hash.
    Prevents same artifact from being both approved and rejected.
    Never modifies source files.
    """
    from pcae.core.backend_invocations import (
        read_latest_review, reject_review, persist_rejection,
    )

    review_id: str = getattr(args, "review_id", "") or ""
    output_hash: str = getattr(args, "output_hash", "") or ""
    operator: str = getattr(args, "operator", "") or ""
    reason: str = getattr(args, "reason", "") or ""

    if not review_id:
        msg = "Missing --review-id"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not output_hash:
        msg = "Missing --output-hash"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not operator:
        msg = "Missing --operator"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not reason:
        msg = "Missing --reason"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    review = read_latest_review()
    if review is None:
        msg = "No review artifact found. Create one with: pcae backend review create"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    # Verify review_id binding
    if review.review_id != review_id:
        msg = f"Review ID mismatch: found {review.review_id!r}, expected {review_id!r}"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    # Verify output_hash binding
    if review.output_hash != output_hash:
        msg = "Output hash mismatch — rejection must bind to exact output hash"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    # Conflict guard: cannot reject an already-approved review
    if review.approved_for_apply:
        msg = "Cannot reject: review is already approved"
        print(json.dumps({"error": msg, "hard_block": True}) if args.json else f"Error: {msg}")
        return 1

    rejection = reject_review(review, operator, reason)

    issues = rejection.validate()
    if issues:
        msg = f"Invalid rejection: {'; '.join(issues)}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    persist_result = persist_rejection(rejection, review)
    if persist_result.get("status") != "written":
        msg = f"Failed to persist rejection: {persist_result.get('error', 'unknown')}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps({
            "rejection": rejection.to_dict(),
            "review": review.to_dict(),
            "persistence": persist_result,
            "no_execution": True,
            "no_source_files_modified": True,
        }, indent=2))
    else:
        print("Backend review rejected")
        print(f"  Rejection ID:  {rejection.rejection_id}")
        print(f"  Review ID:     {rejection.review_id}")
        print(f"  Output hash:   {(rejection.output_hash or '')[:16]}...")
        print(f"  Operator:      {rejection.operator}")
        print(f"  Review state:  {review.review_state}")
        print(f"  Rejected at:   {rejection.rejected_at_utc}")
        print(f"  Artifact:      {persist_result.get('rejection_path', '')}")
        print()
        print("  ✅ Rejection recorded. No source files modified.")
    return 0


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


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94N — Apply plan CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_apply_plan_show(args: argparse.Namespace) -> int:
    """pcae backend apply-plan show --latest [--json]

    Read-only display of latest apply plan metadata.
    Never prints raw backend output or prompt content.
    Never executes apply, never mutates files.
    """
    from pcae.core.backend_invocations import read_latest_apply_plan

    plan = read_latest_apply_plan()
    if plan is None:
        msg = "No apply plans found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print("Apply plan — latest")
        print(f"  Plan ID:         {plan.apply_plan_id}")
        print(f"  Review ID:       {plan.review_id}")
        print(f"  Approval ID:     {plan.approval_id}")
        print(f"  Request ID:      {plan.request_id}")
        print(f"  Phase ID:        {plan.phase_id}")
        print(f"  Backend ID:      {plan.backend_id}")
        print(f"  Output hash:     {plan.output_hash}")
        print(f"  Apply ready:     {plan.apply_ready}")
        print(f"  Rollback req:    {plan.rollback_required}")
        print(f"  Check required:  {plan.check_required}")
        print(f"  Risk level:      {plan.risk_level}")
        print(f"  Operations:      {len(plan.operations)}")
        for i, op in enumerate(plan.operations):
            print(f"    [{i}] {op.operation_type}:{op.target_path}")
        if plan.hard_blocks:
            print(f"  Hard blocks:     {', '.join(plan.hard_blocks)}")
        if plan.missing_evidence:
            print(f"  Missing ev:      {', '.join(plan.missing_evidence)}")
        if plan.warnings:
            print(f"  Warnings:        {', '.join(plan.warnings)}")
        print(f"  Created:         {plan.created_at_utc}")
        print()
        print("  Metadata only. No raw output or prompt content displayed.")
        print("  ⚠️  apply_ready does not mean apply is executed.")
    return 0


def run_backend_apply_plan_create(args: argparse.Namespace) -> int:
    """pcae backend apply-plan create [--json]

    Creates an apply plan artifact bound to a review and output hash.
    Safe defaults: apply_ready=False, rollback_required=True, check_required=True.
    Accepts descriptive operations as metadata only — no patch parsing.
    Never executes apply, never mutates source files.
    """
    import uuid as _uuid
    from pcae.core.backend_invocations import (
        ApplyPlan, ApplyOperation, persist_apply_plan,
        OP_MANUAL, VALID_OPERATIONS, HIGH_RISK_OPS, RISK_MEDIUM,
    )

    review_id: str = getattr(args, "review_id", "") or ""
    approval_id: str = getattr(args, "approval_id", "") or ""
    request_id: str = getattr(args, "request_id", "") or ""
    output_hash: str = getattr(args, "output_hash", "") or ""

    if not review_id:
        msg = "Missing --review-id"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if not output_hash:
        msg = "Missing --output-hash"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    phase_id: str = getattr(args, "phase_id", "") or ""
    backend_id: str = getattr(args, "backend", "") or ""
    ops_raw: list[str] = list(getattr(args, "operation", None) or [])
    ops_file: str = getattr(args, "operations_file", "") or ""

    # Parse descriptive operations — metadata only, no patch parsing
    hard_blocks: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []
    ops: list[ApplyOperation] = []

    # Load from file if provided
    if ops_file:
        import json as _json_mod
        from pathlib import Path as _Path
        fp = _Path(ops_file)
        if not fp.is_file():
            msg = f"Operations file not found: {ops_file}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            raw_ops = _json_mod.loads(fp.read_text())
            if isinstance(raw_ops, list):
                ops_raw = ops_raw + [
                    f"{o.get('operation_type', OP_MANUAL)}:{o.get('target_path', '')}"
                    for o in raw_ops if isinstance(o, dict)
                ]
        except Exception as exc:
            msg = f"Failed to load operations file: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1

    for op_str in ops_raw:
        # Parse "operation_type:target_path" — descriptive metadata only
        if ":" in op_str:
            op_type, _, target = op_str.partition(":")
            op_type = op_type.strip()
            target = target.strip()
        else:
            op_type = op_str.strip()
            target = ""

        if op_type not in VALID_OPERATIONS:
            warnings.append(f"unknown_operation_type:{op_type}")
            op_type = "unknown"

        is_high_risk = op_type in HIGH_RISK_OPS
        if is_high_risk:
            hard_blocks.append(f"high_risk_op:{op_type}:{target}")

        ops.append(ApplyOperation(
            operation_id=f"op-{_uuid.uuid4().hex[:8]}",
            operation_type=op_type,
            target_path=target,
            risk_level=RISK_MEDIUM,
            allowed_by_task_scope=False,
            forbidden=False,
            requires_manual_review=True,
        ))

    if not approval_id:
        missing.append("approval_id")
    if not ops:
        missing.append("operations")

    from datetime import datetime, timezone as _tz
    now = datetime.now(_tz.utc).isoformat()

    plan = ApplyPlan(
        apply_plan_id=f"pl-{_uuid.uuid4().hex[:12]}",
        review_id=review_id,
        approval_id=approval_id,
        request_id=request_id,
        phase_id=phase_id,
        backend_id=backend_id,
        output_hash=output_hash,
        operations=ops,
        hard_blocks=hard_blocks,
        missing_evidence=missing,
        warnings=warnings,
        apply_ready=False,
        rollback_required=True,
        check_required=True,
        created_at_utc=now,
    )

    persist_result = persist_apply_plan(plan)

    if args.json:
        print(json.dumps({
            "plan": plan.to_dict(),
            "persistence": persist_result,
            "no_execution": True,
            "no_apply": True,
            "no_patch_parsing": True,
            "no_source_files_modified": True,
        }, indent=2))
    else:
        print("Apply plan created")
        print(f"  Plan ID:         {plan.apply_plan_id}")
        print(f"  Review ID:       {plan.review_id}")
        print(f"  Approval ID:     {plan.approval_id}")
        print(f"  Output hash:     {plan.output_hash}")
        print(f"  Apply ready:     {plan.apply_ready}")
        print(f"  Rollback req:    {plan.rollback_required}")
        print(f"  Check required:  {plan.check_required}")
        print(f"  Operations:      {len(ops)}")
        if hard_blocks:
            print(f"  Hard blocks:     {', '.join(hard_blocks)}")
        if missing:
            print(f"  Missing ev:      {', '.join(missing)}")
        if persist_result.get("status") == "written":
            print(f"  Persisted to:    {persist_result.get('path', '')}")
        print()
        print("  ✅ Apply plan recorded. No apply executed. No source files modified.")
    return 0


def run_backend_apply_plan_validate(args: argparse.Namespace) -> int:
    """pcae backend apply-plan validate [--plan <path>] [--json]

    Validates latest (or specified) apply plan for readiness.
    Produces a BackendApplyReadinessAssessment.
    Never executes apply, never runs tests, never runs pcae check, never mutates files.
    """
    import json as _json_mod
    from pathlib import Path as _Path
    from pcae.core.backend_invocations import (
        ApplyPlan, ApplyOperation, ReviewArtifact, ApprovalArtifact,
        validate_backend_apply_readiness, persist_apply_readiness,
        read_latest_apply_plan,
    )

    plan_path: str = getattr(args, "plan", "") or ""
    review_path: str = getattr(args, "review", "") or ""
    approval_path: str = getattr(args, "approval", "") or ""

    plan: ApplyPlan | None = None

    if plan_path:
        p = _Path(plan_path)
        if not p.is_file():
            msg = f"Apply plan not found: {plan_path}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            data = _json_mod.loads(p.read_text())
            plan = ApplyPlan(**{k: v for k, v in data.items()
                                 if k in ApplyPlan.__dataclass_fields__})
            ops_raw = data.get("operations", [])
            plan.operations = [
                ApplyOperation(**{k: v for k, v in od.items()
                                   if k in ApplyOperation.__dataclass_fields__})
                for od in ops_raw if isinstance(od, dict)
            ]
        except Exception as exc:
            msg = f"Failed to load apply plan: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
    else:
        plan = read_latest_apply_plan()
        if plan is None:
            msg = "No apply plan found. Use --plan <path> or create one first."
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1

    review: ReviewArtifact | None = None
    if review_path:
        rp = _Path(review_path)
        if rp.is_file():
            try:
                rd = _json_mod.loads(rp.read_text())
                review = ReviewArtifact(**{k: v for k, v in rd.items()
                                            if k in ReviewArtifact.__dataclass_fields__})
            except Exception:
                pass

    approval: ApprovalArtifact | None = None
    if approval_path:
        ap = _Path(approval_path)
        if ap.is_file():
            try:
                ad = _json_mod.loads(ap.read_text())
                approval = ApprovalArtifact(**{k: v for k, v in ad.items()
                                                if k in ApprovalArtifact.__dataclass_fields__})
            except Exception:
                pass

    assessment = validate_backend_apply_readiness(
        plan=plan, review=review, approval=approval,
    )
    persist_result = persist_apply_readiness(assessment)

    if args.json:
        print(json.dumps({
            "assessment": assessment.to_dict(),
            "persistence": persist_result,
            "no_execution": True,
            "no_apply": True,
            "no_tests_run": True,
            "no_pcae_check_run": True,
            "no_source_files_modified": True,
        }, indent=2))
    else:
        print("Apply plan readiness validation")
        print(f"  Assessment ID:     {assessment.assessment_id}")
        print(f"  Plan ID:           {assessment.apply_plan_id}")
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
            print(f"  Assessment saved:  {persist_result.get('path', '')}")
        print()
        print("  ⚠️  Read-only validation. No apply executed. No tests run. No pcae check run.")


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94O — Manual apply package CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_manual_apply_package_show(args: argparse.Namespace) -> int:
    """pcae backend manual-apply-package show --latest [--json]

    Read-only display of latest manual apply package metadata.
    Never executes apply, never mutates files.
    """
    from pcae.core.backend_invocations import read_latest_manual_apply_package

    pkg = read_latest_manual_apply_package()
    if pkg is None:
        msg = "No manual apply packages found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(pkg.to_dict(), indent=2))
    else:
        print("Manual apply package — latest")
        print(f"  Package ID:        {pkg.package_id}")
        print(f"  Apply plan ID:     {pkg.apply_plan_id}")
        print(f"  Review ID:         {pkg.review_id}")
        print(f"  Approval ID:       {pkg.approval_id}")
        print(f"  Request ID:        {pkg.request_id}")
        print(f"  Phase ID:          {pkg.phase_id}")
        print(f"  Output hash:       {pkg.output_hash}")
        print(f"  Readiness status:  {pkg.readiness_status}")
        print(f"  Apply ready:       {pkg.apply_ready}")
        print(f"  Rollback req:      {pkg.rollback_required}")
        print(f"  Operations:        {len(pkg.operations)}")
        for op in pkg.operations:
            print(f"    - {op}")
        if pkg.hard_blocks:
            print(f"  Hard blocks:       {', '.join(pkg.hard_blocks)}")
        if pkg.missing_evidence:
            print(f"  Missing ev:        {', '.join(pkg.missing_evidence)}")
        if pkg.warnings:
            print(f"  Warnings:          {', '.join(pkg.warnings)}")
        print(f"  No execution:      {pkg.no_execution_performed}")
        print(f"  Created:           {pkg.created_at_utc}")
        print()
        print("  Package metadata only. No raw prompt/output content displayed.")
        print("  ⚠️  Package generation does not execute apply.")
    return 0


def run_backend_manual_apply_package_create(args: argparse.Namespace) -> int:
    """pcae backend manual-apply-package create [--apply-plan <path>] [--readiness <path>] [--json]

    Creates a manual apply package from an apply plan and optional readiness assessment.
    Persists as JSON + Markdown under .pcae/backend-manual-apply-packages/.
    Never executes apply, never mutates source files.
    """
    import json as _json_mod
    from pathlib import Path as _Path
    from pcae.core.backend_invocations import (
        ApplyPlan, ApplyOperation, BackendApplyReadinessAssessment,
        ReviewArtifact, ApprovalArtifact,
        create_backend_manual_apply_package, persist_manual_apply_package,
        read_latest_apply_plan, read_latest_apply_readiness,
    )

    plan_path: str = getattr(args, "apply_plan", "") or ""
    readiness_path: str = getattr(args, "readiness", "") or ""
    review_path: str = getattr(args, "review", "") or ""
    approval_path: str = getattr(args, "approval", "") or ""
    operator_notes: str = getattr(args, "operator_notes", "") or ""
    rollback_instructions: str = getattr(args, "rollback_instructions", "") or ""

    # Load apply plan
    plan: ApplyPlan | None = None
    if plan_path:
        p = _Path(plan_path)
        if not p.is_file():
            msg = f"Apply plan not found: {plan_path}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            data = _json_mod.loads(p.read_text())
            plan = ApplyPlan(**{k: v for k, v in data.items()
                                 if k in ApplyPlan.__dataclass_fields__})
            ops_raw = data.get("operations", [])
            plan.operations = [
                ApplyOperation(**{k: v for k, v in od.items()
                                   if k in ApplyOperation.__dataclass_fields__})
                for od in ops_raw if isinstance(od, dict)
            ]
        except Exception as exc:
            msg = f"Failed to load apply plan: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
    else:
        plan = read_latest_apply_plan()

    # Load readiness assessment
    assessment: BackendApplyReadinessAssessment | None = None
    if readiness_path:
        rp = _Path(readiness_path)
        if rp.is_file():
            try:
                rd = _json_mod.loads(rp.read_text())
                assessment = BackendApplyReadinessAssessment.from_dict(rd)
            except Exception:
                pass
    else:
        assessment = read_latest_apply_readiness()

    # Load optional review
    review: ReviewArtifact | None = None
    if review_path:
        rp = _Path(review_path)
        if rp.is_file():
            try:
                rd = _json_mod.loads(rp.read_text())
                review = ReviewArtifact(**{k: v for k, v in rd.items()
                                            if k in ReviewArtifact.__dataclass_fields__})
            except Exception:
                pass

    # Load optional approval
    approval: ApprovalArtifact | None = None
    if approval_path:
        ap = _Path(approval_path)
        if ap.is_file():
            try:
                ad = _json_mod.loads(ap.read_text())
                approval = ApprovalArtifact(**{k: v for k, v in ad.items()
                                                if k in ApprovalArtifact.__dataclass_fields__})
            except Exception:
                pass

    pkg = create_backend_manual_apply_package(
        plan=plan,
        assessment=assessment,
        review=review,
        approval=approval,
        operator_notes=operator_notes,
        rollback_instructions=rollback_instructions,
    )
    persist_result = persist_manual_apply_package(pkg)

    if args.json:
        print(json.dumps({
            "package": pkg.to_dict(),
            "persistence": persist_result,
            "no_execution": True,
            "no_apply": True,
            "no_patch_parsing": True,
            "no_source_files_modified": True,
            "no_automatic_tests": True,
            "no_automatic_pcae_check": True,
        }, indent=2))
    else:
        print("Manual apply package created")
        print(f"  Package ID:        {pkg.package_id}")
        print(f"  Apply plan ID:     {pkg.apply_plan_id}")
        print(f"  Output hash:       {pkg.output_hash}")
        print(f"  Readiness status:  {pkg.readiness_status}")
        print(f"  Apply ready:       {pkg.apply_ready}")
        print(f"  Operations:        {len(pkg.operations)}")
        if pkg.hard_blocks:
            print(f"  Hard blocks:       {', '.join(pkg.hard_blocks)}")
        if pkg.missing_evidence:
            print(f"  Missing ev:        {', '.join(pkg.missing_evidence)}")
        if persist_result.get("status") == "written":
            print(f"  JSON:              {persist_result.get('json_path', '')}")
            print(f"  Markdown:          {persist_result.get('md_path', '')}")
        print()
        print("  ✅ Package created. No apply executed. No source files modified.")
        print("  ⚠️  Manual apply instructions are advisory — human action required.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Q — Backend lifecycle demo CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_demo_mock_lifecycle(args: argparse.Namespace) -> int:
    """pcae backend demo mock-lifecycle [--json] [--negative]

    Runs a complete end-to-end mock backend lifecycle demo.
    Uses mock backend only. No real backend invocation.
    No apply execution. No file mutation. No subprocess. No network.
    """
    negative: bool = getattr(args, "negative", False) or False
    phase_id: str = getattr(args, "phase_id", "94Q") or "94Q"
    task_id: str = getattr(args, "task_id", "") or ""

    demo, steps = run_mock_lifecycle_demo(
        phase_id=phase_id,
        task_id=task_id,
        forbidden_path_check=negative,
    )

    persist_result = persist_lifecycle_demo(demo)

    if args.json:
        print(json.dumps({
            "demo": demo.to_dict(),
            "steps": {k: v for k, v in steps.items() if k != "demo"},
            "persistence": persist_result,
            "no_real_backend_invoked": True,
            "no_apply_execution": True,
            "no_file_mutation": True,
            "no_subprocess": True,
            "no_network": True,
            "no_shell_interception": True,
        }, indent=2))
    else:
        print(f"Mock lifecycle demo — {demo.lifecycle_status}")
        print(f"  Demo ID:            {demo.demo_id}")
        print(f"  Phase ID:           {demo.phase_id}")
        print(f"  Backend:            {demo.backend_id}")
        print(f"  Request ID:         {demo.request_id}")
        print(f"  Prompt hash:        {demo.prompt_hash[:16]}...")
        print(f"  Output hash:        {demo.output_hash[:16]}...")
        print(f"  Audit ID:           {demo.audit_id}")
        print(f"  Trust assessment:   {demo.trust_assessment_id}")
        print(f"  Review ID:          {demo.review_id}")
        if demo.approval_id:
            print(f"  Approval ID:        {demo.approval_id}")
        if demo.rejection_id:
            print(f"  Rejection ID:       {demo.rejection_id}")
        print(f"  Apply plan ID:      {demo.apply_plan_id}")
        print(f"  Readiness assess:   {demo.apply_readiness_assessment_id}")
        print(f"  Lifecycle status:   {demo.lifecycle_status}")
        if demo.hard_blocks:
            print(f"  Hard blocks:        {', '.join(demo.hard_blocks)}")
        if demo.missing_evidence:
            print(f"  Missing evidence:   {', '.join(demo.missing_evidence)}")
        if demo.warnings:
            print(f"  Warnings:           {', '.join(demo.warnings)}")
        if persist_result.get("status") == "written":
            print(f"  Artifact:           {persist_result.get('path', '')}")
        print()
        print("  Mock lifecycle demo completed.")
        print("  No real backend invoked.")
        print("  No files modified.")
        print("  No apply executed.")
        print("  Output remains quarantined.")
        if negative:
            print("  ⚠️  Negative path exercised — expected hard blocks present.")
    return 0


def run_backend_demo_show(args: argparse.Namespace) -> int:
    """pcae backend demo show --latest [--json]

    Shows the latest lifecycle demo summary. Read-only.
    """
    demo = read_latest_lifecycle_demo()

    if demo is None:
        msg = "No lifecycle demo found. Run 'pcae backend demo mock-lifecycle' first."
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(demo.to_dict(), indent=2))
    else:
        print(f"Latest lifecycle demo — {demo.lifecycle_status}")
        print(f"  Demo ID:            {demo.demo_id}")
        print(f"  Phase ID:           {demo.phase_id}")
        print(f"  Backend:            {demo.backend_id}")
        print(f"  Request ID:         {demo.request_id}")
        print(f"  Prompt hash:        {demo.prompt_hash[:16]}...")
        print(f"  Output hash:        {demo.output_hash[:16]}...")
        print(f"  Audit ID:           {demo.audit_id}")
        print(f"  Trust assessment:   {demo.trust_assessment_id}")
        print(f"  Review ID:          {demo.review_id}")
        if demo.approval_id:
            print(f"  Approval ID:        {demo.approval_id}")
        if demo.rejection_id:
            print(f"  Rejection ID:       {demo.rejection_id}")
        print(f"  Apply plan ID:      {demo.apply_plan_id}")
        print(f"  Readiness assess:   {demo.apply_readiness_assessment_id}")
        print(f"  Lifecycle status:   {demo.lifecycle_status}")
        if demo.hard_blocks:
            print(f"  Hard blocks:        {', '.join(demo.hard_blocks)}")
        if demo.missing_evidence:
            print(f"  Missing evidence:   {', '.join(demo.missing_evidence)}")
        if demo.warnings:
            print(f"  Warnings:           {', '.join(demo.warnings)}")
        print(f"  No real backend:    {demo.no_real_backend_invoked}")
        print(f"  No apply:           {demo.no_apply_execution}")
        print(f"  No file mutation:   {demo.no_file_mutation}")
        print(f"  Created:            {demo.created_at_utc}")
        print()
        print("  Output remains quarantined. No files modified.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94T — Real backend adapter preflight CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_list(args: argparse.Namespace) -> int:
    """pcae backend adapter list [--json]

    Read-only. Lists all adapter contracts. Never invokes backends.
    """
    reg = get_default_adapter_registry()
    entries = []
    for bid, c in sorted(reg.items()):
        entries.append({
            "backend_id": bid,
            "adapter_id": c.adapter_id,
            "backend_type": c.backend_type,
            "invocation_mode": c.invocation_mode,
            "supports_artifact_only": c.supports_artifact_only,
            "requires_secrets": c.requires_secrets,
            "display_name": c.display_name,
        })

    if args.json:
        print(json.dumps({"adapters": entries, "count": len(entries),
                          "no_real_backend_invoked": True}, indent=2))
    else:
        print(f"Backend adapter registry — {len(entries)} adapter(s)")
        for e in entries:
            mode_label = e["invocation_mode"]
            secrets = "secrets" if e["requires_secrets"] else "no-secrets"
            print(f"  {e['backend_id']:20s}  type={e['backend_type']:22s}  "
                  f"mode={mode_label:16s}  {secrets}")
        print()
        print("  ⚠️  All real adapters are preflight-only. No backend invocation capability.")
    return 0


def run_backend_adapter_show(args: argparse.Namespace) -> int:
    """pcae backend adapter show --backend <id> [--json]

    Read-only. Shows adapter contract details. Never invokes backends.
    """
    backend_id: str = getattr(args, "backend", "") or ""
    if not backend_id:
        msg = "Missing --backend <id>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    reg = get_default_adapter_registry()
    if backend_id not in reg:
        msg = f"Unknown backend: {backend_id!r}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    c = reg[backend_id]
    safety = c.safety_capabilities

    if args.json:
        print(json.dumps({
            "adapter": c.to_dict(),
            "no_real_backend_invoked": True,
            "no_subprocess": True,
            "no_network": True,
        }, indent=2))
    else:
        print(f"Backend adapter: {c.backend_id}")
        print(f"  Adapter ID:          {c.adapter_id}")
        print(f"  Display name:        {c.display_name}")
        print(f"  Backend type:        {c.backend_type}")
        print(f"  Invocation mode:     {c.invocation_mode}")
        print(f"  Artifact only:       {c.supports_artifact_only}")
        print(f"  Streaming:           {c.supports_streaming}")
        print(f"  Timeout support:     {c.supports_timeout}")
        print(f"  Session reuse:       {c.supports_session_reuse}")
        print(f"  Requires secrets:    {c.requires_secrets}")
        if c.required_env_keys:
            print(f"  Required env keys:   {', '.join(c.required_env_keys)}")
        print()
        print("  Safety profile:")
        print(f"    Human approval:    {safety.requires_human_approval}")
        print(f"    Permission broker: {safety.requires_permission_broker}")
        print(f"    Shell gate:        {safety.requires_shell_gate}")
        print(f"    Output quarantine: {safety.requires_output_quarantine}")
        print(f"    Audit:             {safety.requires_audit}")
        print(f"    Timeout:           {safety.requires_timeout}")
        print(f"    Secret redaction:  {safety.requires_secret_redaction}")
        print(f"    Bypass detection:  {safety.requires_bypass_detection}")
        print(f"    No-apply guarantee:{safety.supports_no_apply_guarantee}")
        print()
        print("  ⚠️  Read-only adapter metadata. No backend invocation capability.")
    return 0


def run_backend_adapter_preflight(args: argparse.Namespace) -> int:
    """pcae backend adapter preflight --backend <id> [--json]

    Model-only and env-presence-only preflight. Never invokes backends,
    never spawns subprocess, never calls network, never prints secrets.
    """
    backend_id: str = getattr(args, "backend", "") or ""
    if not backend_id:
        msg = "Missing --backend <id>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    reg = get_default_adapter_registry()
    if backend_id not in reg:
        msg = f"Unknown backend: {backend_id!r}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    contract = reg[backend_id]
    r = validate_backend_adapter_preflight(contract)

    if args.json:
        print(json.dumps({
            "preflight": r.to_dict(),
            "no_real_backend_invoked": True,
            "no_subprocess": True,
            "no_network": True,
        }, indent=2))
    else:
        print(f"Backend adapter preflight: {r.backend_id}")
        print(f"  Status:              {r.status}")
        print(f"  Ready:               {'yes' if r.ready else 'no'}")
        if r.missing_env_keys:
            print(f"  Missing env:         {', '.join(r.missing_env_keys)}")
        if r.present_env_keys_redacted:
            print(f"  Present env:         {', '.join(r.present_env_keys_redacted)}")
        if r.hard_blocks:
            print(f"  Hard blocks:         {', '.join(r.hard_blocks)}")
        if r.unsafe_conditions:
            print(f"  Unsafe conditions:   {', '.join(r.unsafe_conditions)}")
        if r.warnings:
            print(f"  Warnings:            {', '.join(r.warnings)}")
        print(f"  Human approval:      {r.requires_human_approval}")
        print(f"  Broker required:     {r.requires_broker}")
        print(f"  Shell gate required: {r.requires_shell_gate}")
        print(f"  Bypass detected:     {r.bypass_permissions_detected}")
        print(f"  No real backend:     {r.no_real_backend_invoked}")
        print(f"  No subprocess:       {r.no_subprocess}")
        print(f"  No network:          {r.no_network}")
        print()
        print("  ⚠️  Model-only preflight. No backend was invoked.")
    # ── Phase 94U: persist if --save ──────────────────────────────────
    save: bool = getattr(args, "save", False) or False
    if save:
        artifact = BackendAdapterPreflightArtifact.from_preflight_result(
            r, source_command=f"pcae backend adapter preflight --backend {backend_id}",
        )
        persist_result = persist_backend_adapter_preflight_artifact(artifact)
        if args.json:
            # Already printed JSON above; add persistence result
            pass
        else:
            if persist_result.get("status") == "written":
                print(f"  Artifact saved:     {persist_result.get('path', '')}")
                print(f"  Digest:             {persist_result.get('record_digest', '')[:16]}...")

    return 0 if r.ready else 1


def run_backend_adapter_preflight_show(args: argparse.Namespace) -> int:
    """pcae backend adapter preflight show --latest [--json]

    Read-only. Shows the latest persisted preflight artifact.
    """
    artifact = load_latest_backend_adapter_preflight_artifact()
    if artifact is None:
        msg = "No preflight artifacts found. Run 'pcae backend adapter preflight --backend <id> --save' first."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(artifact.to_dict(), indent=2))
    else:
        print(f"Latest preflight artifact: {artifact.backend_id}")
        print(f"  Artifact ID:         {artifact.artifact_id}")
        print(f"  Preflight ID:        {artifact.preflight_id}")
        print(f"  Status:              {artifact.status}")
        print(f"  Ready:               {'yes' if artifact.ready else 'no'}")
        if artifact.missing_env_keys:
            print(f"  Missing env:         {', '.join(artifact.missing_env_keys)}")
        if artifact.present_env_keys_redacted:
            print(f"  Present env:         {', '.join(artifact.present_env_keys_redacted)}")
        if artifact.hard_blocks:
            print(f"  Hard blocks:         {', '.join(artifact.hard_blocks)}")
        print(f"  Digest:              {artifact.record_digest[:16]}...")
        print(f"  No real backend:     {artifact.no_real_backend_invoked}")
        print(f"  No subprocess:       {artifact.no_subprocess}")
        print(f"  No network:          {artifact.no_network}")
        print(f"  Created:             {artifact.created_at_utc}")
    return 0


def run_backend_adapter_preflight_verify(args: argparse.Namespace) -> int:
    """pcae backend adapter preflight verify --latest [--json]

    Read-only. Verifies the latest persisted preflight artifact integrity.
    """
    artifact = load_latest_backend_adapter_preflight_artifact()
    if artifact is None:
        msg = "No preflight artifacts found to verify."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    result = verify_backend_adapter_preflight_artifact(artifact)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"Preflight artifact verified: {artifact.backend_id}")
            print(f"  Artifact ID:  {artifact.artifact_id}")
            print(f"  Digest:       {artifact.record_digest[:16]}...")
            print(f"  Status:       valid")
        else:
            print(f"Preflight artifact verification FAILED: {artifact.backend_id}")
            for issue in result["issues"]:
                print(f"  - {issue}")
    return 0 if result["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Y — Real adapter invocation approval CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_approval_show(args: argparse.Namespace) -> int:
    """pcae backend adapter approval show --latest [--json]

    Read-only. Shows the latest persisted approval artifact.
    Approval-create CLI is deferred to 94Z.
    """
    approval = load_latest_real_adapter_invocation_approval()
    if approval is None:
        msg = "No approval artifacts found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    if args.json:
        print(json.dumps(approval.to_dict(), indent=2))
    else:
        print(f"Latest invocation approval: {approval.backend_id}")
        print(f"  Approval ID:         {approval.approval_id}")
        print(f"  Decision:            {approval.decision}")
        print(f"  Effective:           {'yes' if approval.approval_effective else 'no'}")
        print(f"  Operator:            {approval.operator}")
        print(f"  Prompt hash:         {approval.prompt_hash[:16] if approval.prompt_hash else 'N/A'}...")
        print(f"  Preflight digest:    {approval.preflight_digest[:16] if approval.preflight_digest else 'N/A'}...")
        print(f"  Hard blocks:         {approval.hard_blocks_present}")
        print(f"  Accepted risk:       {approval.accepted_risk}")
        print(f"  Digest:              {approval.record_digest[:16]}...")
        print(f"  Approved at:         {approval.approved_at_utc}")
    return 0


def run_backend_adapter_approval_verify(args: argparse.Namespace) -> int:
    """pcae backend adapter approval verify --latest [--json]

    Read-only. Verifies the latest approval artifact integrity.
    """
    approval = load_latest_real_adapter_invocation_approval()
    if approval is None:
        msg = "No approval artifacts found to verify."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    result = verify_real_adapter_invocation_approval(approval)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"Approval artifact verified: {approval.backend_id}")
            print(f"  Digest:   {approval.record_digest[:16]}...")
            print(f"  Status:   valid")
        else:
            print(f"Approval verification FAILED: {approval.backend_id}")
            for issue in result["issues"]:
                print(f"  - {issue}")
    return 0 if result["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 94Z — Real adapter invocation plan CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_plan_show(args: argparse.Namespace) -> int:
    """pcae backend adapter plan show --latest [--json]"""
    plan = load_latest_real_adapter_invocation_plan()
    if plan is None:
        msg = "No invocation plan artifacts found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if args.json:
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(f"Latest invocation plan: {plan.backend_id}")
        print(f"  Plan ID:             {plan.plan_id}")
        print(f"  Preflight ID:        {plan.preflight_artifact_id}")
        print(f"  Approval ID:         {plan.approval_id}")
        print(f"  Timeout:             {plan.timeout_seconds}s")
        print(f"  No auto-apply:       {plan.no_auto_apply}")
        print(f"  No commit:           {plan.no_commit_authorization}")
        print(f"  No push:             {plan.no_push_authorization}")
        print(f"  Real allowed:        {plan.real_backend_invocation_allowed}")
        print(f"  Execution ready:     {plan.execution_ready}")
        if plan.hard_blocks:
            print(f"  Hard blocks:         {', '.join(plan.hard_blocks)}")
        print(f"  Digest:              {plan.record_digest[:16]}...")
    return 0


def run_backend_adapter_plan_verify(args: argparse.Namespace) -> int:
    """pcae backend adapter plan verify --latest [--json]"""
    plan = load_latest_real_adapter_invocation_plan()
    if plan is None:
        msg = "No invocation plan artifacts found to verify."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    result = verify_real_adapter_invocation_plan(plan)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"Plan verified: {plan.backend_id} — valid")
        else:
            print(f"Plan verification FAILED: {plan.backend_id}")
            for issue in result["issues"]:
                print(f"  - {issue}")
    return 0 if result["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95A — Artifact-only real invocation dry-run boundary CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_dry_run_evaluate(args: argparse.Namespace) -> int:
    """pcae backend adapter dry-run evaluate --plan-artifact <path> [--save] [--json]

    Evaluates evidence chain without executing anything.
    """
    from pathlib import Path as _P
    plan_path: str = getattr(args, "plan_artifact", "") or ""
    save: bool = getattr(args, "save", False) or False

    if not plan_path:
        msg = "Missing --plan-artifact <path>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    p = _P(plan_path)
    if not p.is_file():
        msg = f"Plan artifact not found: {plan_path}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    try:
        data = json.loads(p.read_text())
        plan = RealAdapterInvocationPlan.from_dict(data)
    except Exception as exc:
        msg = f"Failed to load plan: {exc}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    # ── Load runtime evidence if provided (Phase 95E) ──────────────────
    runtime_ev: ClaudeRuntimeEvidence | None = None
    re_path: str = getattr(args, "runtime_evidence", "") or ""
    if re_path:
        rp = _P(re_path)
        if not rp.is_file():
            msg = f"Runtime evidence not found: {re_path}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1
        try:
            re_data = json.loads(rp.read_text())
            runtime_ev = ClaudeRuntimeEvidence.from_dict(re_data)
        except Exception as exc:
            msg = f"Failed to load runtime evidence: {exc}"
            print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
            return 1

    assessment = evaluate_artifact_only_real_invocation_dry_run(
        plan=plan, runtime_evidence=runtime_ev,
    )

    if save:
        persist_artifact_only_real_invocation_dry_run_assessment(assessment)

    if args.json:
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        print(f"Dry-run assessment: {assessment.assessment_id}")
        print(f"  Backend:             {assessment.backend_id}")
        print(f"  Dry-run only:        {assessment.dry_run_only}")
        print(f"  Evidence valid:      {assessment.evidence_chain_valid}")
        print(f"  Execution allowed:   {assessment.execution_allowed}")
        print(f"  Execution ready:     {assessment.execution_ready}")
        if assessment.hard_blocks:
            print(f"  Hard blocks:         {', '.join(assessment.hard_blocks)}")
        if assessment.deny_reasons:
            print(f"  Deny reasons:        {', '.join(assessment.deny_reasons)}")
        if assessment.runtime_evidence_id:
            print(f"  Runtime evidence:    {assessment.runtime_evidence_id} "
                  f"({'valid' if assessment.runtime_evidence_valid else 'invalid'})")
            print(f"  Bypass state:        {assessment.runtime_bypass_permissions_state}")
            print(f"  Broker decision:     {assessment.runtime_broker_decision}")
            print(f"  Shell-gate decision: {assessment.runtime_shell_gate_decision}")
        else:
            print(f"  Runtime evidence:    missing")
        print(f"  No real backend:     {assessment.no_real_backend_invoked}")
        print(f"  No adapter executed: {assessment.no_adapter_executed}")
        print(f"  No subprocess:       {assessment.no_subprocess}")
        print(f"  No network:          {assessment.no_network}")
        print()
        print("  ⚠️  Dry-run only. No backend was invoked. No adapter was executed.")
    return 0


def run_backend_adapter_dry_run_show(args: argparse.Namespace) -> int:
    """pcae backend adapter dry-run show --latest [--json]"""
    a = load_latest_artifact_only_real_invocation_dry_run_assessment()
    if a is None:
        msg = "No dry-run assessments found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if args.json:
        print(json.dumps(a.to_dict(), indent=2))
    else:
        print(f"Latest dry-run assessment: {a.backend_id}")
        print(f"  Execution allowed:   {a.execution_allowed}")
        print(f"  Evidence valid:      {a.evidence_chain_valid}")
        print(f"  Dry-run only:        {a.dry_run_only}")
        if a.hard_blocks:
            print(f"  Hard blocks:         {', '.join(a.hard_blocks)}")
        print(f"  Digest:              {a.record_digest[:16]}...")
    return 0


def run_backend_adapter_dry_run_verify(args: argparse.Namespace) -> int:
    """pcae backend adapter dry-run verify --latest [--json]"""
    a = load_latest_artifact_only_real_invocation_dry_run_assessment()
    if a is None:
        msg = "No dry-run assessments found to verify."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    result = verify_artifact_only_real_invocation_dry_run_assessment(a)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Dry-run assessment verified" if result["valid"] else "Verification FAILED")
        for issue in result["issues"]:
            print(f"  - {issue}")
    return 0 if result["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95C — Claude runtime evidence CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_runtime_evidence_show(args: argparse.Namespace) -> int:
    """pcae backend adapter runtime-evidence show --latest [--json]"""
    e = load_latest_claude_runtime_evidence()
    if e is None:
        msg = "No runtime evidence artifacts found."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    if args.json:
        print(json.dumps(e.to_dict(), indent=2))
    else:
        print(f"Latest runtime evidence: {e.backend_id}")
        print(f"  Evidence ID:         {e.runtime_evidence_id}")
        print(f"  Profile:             {e.runtime_profile}")
        print(f"  Command:             {e.command_identity}")
        print(f"  Bypass state:        {e.bypass_permissions_state}")
        print(f"  Confidence:          {e.confidence}")
        print(f"  Evidence source:     {e.evidence_source}")
        if e.hard_blocks:
            print(f"  Hard blocks:         {', '.join(e.hard_blocks)}")
        print(f"  No real backend:     {e.no_real_backend_invoked}")
        print(f"  Digest:              {e.record_digest[:16]}...")
    return 0


def run_backend_adapter_runtime_evidence_verify(args: argparse.Namespace) -> int:
    """pcae backend adapter runtime-evidence verify --latest [--json]"""
    e = load_latest_claude_runtime_evidence()
    if e is None:
        msg = "No runtime evidence artifacts found to verify."
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1
    result = verify_claude_runtime_evidence(e)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Runtime evidence verified" if result["valid"] else "Verification FAILED")
        for issue in result["issues"]:
            print(f"  - {issue}")
    return 0 if result["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95D — Claude runtime evidence import CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_runtime_evidence_import(args: argparse.Namespace) -> int:
    """pcae backend adapter runtime-evidence import --from-json <path> [--json]"""
    json_path: str = getattr(args, "from_json", "") or ""
    if not json_path:
        msg = "Missing --from-json <path>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    evidence, result = import_claude_runtime_evidence_from_json(json_path)
    if evidence is None:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Import failed: {result.get('error', 'unknown error')}")
            if result.get("hard_blocks"):
                print(f"  Hard blocks:    {', '.join(result['hard_blocks'])}")
            if result.get("details"):
                print(f"  Details:        {', '.join(result['details'][:3])}")
        return 1

    persist = persist_claude_runtime_evidence(evidence)

    if args.json:
        print(json.dumps({
            "evidence": evidence.to_dict(),
            "persistence": persist,
            "status": "imported",
            "no_real_backend_invoked": True,
            "no_live_inspection": True,
        }, indent=2))
    else:
        print(f"Runtime evidence imported: {evidence.backend_id}")
        print(f"  Evidence ID:      {evidence.runtime_evidence_id}")
        print(f"  Profile:          {evidence.runtime_profile}")
        print(f"  Bypass state:     {evidence.bypass_permissions_state}")
        print(f"  Evidence source:  {evidence.evidence_source}")
        print(f"  Digest:           {evidence.record_digest[:16]}...")
        if persist.get("status") == "written":
            print(f"  Artifact saved:   {persist.get('path', '')}")
        print()
        print("  ✅ Imported from explicit JSON only. No live runtime inspection.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95F — Stat-only runtime detector CLI
# ═══════════════════════════════════════════════════════════════════════════


def run_backend_adapter_runtime_evidence_detect_stat_only(args: argparse.Namespace) -> int:
    """pcae backend adapter runtime-evidence detect-stat-only --config <path> [--save] [--json]"""
    from pathlib import Path as _P
    config_path: str = getattr(args, "config", "") or ""
    save: bool = getattr(args, "save", False) or False

    if not config_path:
        msg = "Missing --config <path>"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    cp = _P(config_path)
    if not cp.is_file():
        msg = f"Config file not found: {config_path}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    try:
        config_data = json.loads(cp.read_text())
        config = ClaudeRuntimeDetectionConfig.from_dict(config_data)
    except Exception as exc:
        msg = f"Failed to load config: {exc}"
        print(json.dumps({"error": msg}) if args.json else f"Error: {msg}")
        return 1

    evidence = detect_claude_runtime_evidence_stat_only(config)

    if save:
        evidence.record_digest = evidence.compute_digest()
        persist_claude_runtime_evidence(evidence)

    if args.json:
        print(json.dumps({
            "evidence": evidence.to_dict(),
            "stat_only": True,
            "no_execution": True,
        }, indent=2))
    else:
        print(f"Stat-only detection: {evidence.backend_id}")
        print(f"  Evidence ID:       {evidence.runtime_evidence_id}")
        print(f"  Profile:           {evidence.runtime_profile}")
        print(f"  Command path:      {evidence.declared_command_path}")
        print(f"  Command hash:      {evidence.declared_command_path_hash[:16] if evidence.declared_command_path_hash else 'N/A'}...")
        print(f"  Bypass state:      {evidence.bypass_permissions_state}")
        print(f"  Confidence:        {evidence.confidence}")
        if evidence.hard_blocks:
            print(f"  Hard blocks:       {', '.join(evidence.hard_blocks)}")
        print(f"  Stat-only:         yes")
        print(f"  Executed command:  no")
        print(f"  Subprocess:        no")
        print(f"  Network:           no")
        print()
        print("  ⚠️  Stat-only detection. No command was executed.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95L — Artifact-only invocation dry-run CLI
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ArtifactOnlyInvocationCommandBoundary,
    ArtifactOnlyInvocationCommandBoundaryAssessment,
    validate_artifact_only_invocation_command_boundary,
    verify_artifact_only_invocation_command_boundary,
    persist_artifact_only_invocation_command_boundary_assessment,
    verify_artifact_only_invocation_command_boundary_assessment,
    load_latest_artifact_only_invocation_command_boundary_assessment,
)


def _abort(msg: str, args: argparse.Namespace) -> int:
    """Print an error and return exit code 1. Respects --json."""
    if getattr(args, "json", False):
        print(json.dumps({"error": msg}))
    else:
        print(f"Error: {msg}")
    return 1


def _load_boundary(path: str, args: argparse.Namespace) -> tuple[
    "ArtifactOnlyInvocationCommandBoundary | None", int
]:
    """Load and verify a boundary artifact from an explicit path."""
    from pathlib import Path as _P
    p = _P(path)
    if not p.is_file():
        if p.is_dir():
            return None, _abort(f"Boundary path is a directory: {path}", args)
        return None, _abort(f"Boundary file not found: {path}", args)
    try:
        data = json.loads(p.read_text())
    except Exception as exc:
        return None, _abort(f"Invalid JSON in boundary file: {exc}", args)
    try:
        boundary = ArtifactOnlyInvocationCommandBoundary.from_dict(data)
    except Exception as exc:
        return None, _abort(f"Failed to load boundary: {exc}", args)
    # Verify digest if present
    if boundary.record_digest:
        v = verify_artifact_only_invocation_command_boundary(boundary)
        if not v["valid"]:
            return None, _abort(f"Boundary verification failed: {v['issues']}", args)
    return boundary, 0


def _print_assessment_text(assessment: ArtifactOnlyInvocationCommandBoundaryAssessment) -> None:
    """Print assessment in human-readable text format."""
    print(f"Command Boundary Assessment: {assessment.assessment_id}")
    print(f"  Decision:            {assessment.decision}")
    print(f"  Ready:               {'yes' if assessment.ready else 'no'}")
    print(f"  Command mode:        {assessment.command_mode}")
    if assessment.hard_blocks:
        print(f"  Hard blocks:         {', '.join(assessment.hard_blocks)}")
    if assessment.warnings:
        print(f"  Warnings:            {', '.join(assessment.warnings)}")
    if assessment.missing_inputs:
        print(f"  Missing inputs:      {', '.join(assessment.missing_inputs)}")
    if assessment.failure_classifications:
        print(f"  Failures:            {', '.join(assessment.failure_classifications)}")
    print(f"  Evidence chain:      {'ready' if assessment.evidence_chain_ready else 'incomplete'}")
    print(f"  Broker/shell-gate:   {'ready' if assessment.broker_shell_gate_ready else 'not ready'}")
    print(f"  Quarantine:          {'ready' if assessment.output_quarantine_ready else 'missing'}")
    print(f"  Audit:               {'ready' if assessment.audit_ready else 'missing'}")
    print(f"  Timeout:             {'ready' if assessment.timeout_ready else 'missing'}")
    print(f"  Execution allowed:   {'yes' if assessment.execution_allowed else 'no'}")
    print(f"  Execute supported:   {'yes' if assessment.execute_supported else 'no'}")
    print(f"  Dry-run only:        {'yes' if assessment.dry_run_only else 'no'}")
    print(f"  Real backend:        {'yes' if not assessment.no_real_backend_invoked else 'no'}")
    print(f"  Adapter executed:    {'yes' if not assessment.no_adapter_executed else 'no'}")
    print(f"  Subprocess:          {'yes' if not assessment.no_subprocess else 'no'}")
    print(f"  Network:             {'yes' if not assessment.no_network else 'no'}")
    print(f"  Repo mutation:       {'yes' if not assessment.no_repo_mutation else 'no'}")
    print(f"  Apply:               {'yes' if not assessment.no_apply else 'no'}")
    print(f"  Patch parsing:       {'yes' if not assessment.no_patch_parsing else 'no'}")
    print(f"  Commit/push auth:    {'yes' if not assessment.no_commit_push_authorization else 'no'}")
    print(f"  Telegram inbound:    {'yes' if not assessment.no_telegram_inbound else 'no'}")
    print()
    print("  ⚠️  Dry-run only. No backend was invoked. No adapter was executed.")


def run_backend_invoke_artifact_only_dry_run(args: argparse.Namespace) -> int:
    """pcae backend invoke artifact-only dry-run --boundary <path> [--save] [--json]

    Loads a boundary artifact, validates it, prints assessment.
    Never executes anything.
    """
    boundary_path: str = getattr(args, "boundary", "") or ""
    save: bool = getattr(args, "save", False) or False

    if not boundary_path:
        return _abort("Missing --boundary <path>", args)

    boundary, code = _load_boundary(boundary_path, args)
    if boundary is None:
        return code

    assessment = validate_artifact_only_invocation_command_boundary(boundary)

    if save:
        persist_artifact_only_invocation_command_boundary_assessment(assessment)

    if getattr(args, "json", False):
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        _print_assessment_text(assessment)
    return 0


def run_backend_invoke_artifact_only_show(args: argparse.Namespace) -> int:
    """pcae backend invoke artifact-only show --latest [--json]

    Shows the latest persisted assessment.
    """
    assessment = load_latest_artifact_only_invocation_command_boundary_assessment()
    if assessment is None:
        return _abort("No latest assessment found. Run a dry-run first.", args)

    if getattr(args, "json", False):
        print(json.dumps(assessment.to_dict(), indent=2))
    else:
        _print_assessment_text(assessment)
    return 0


def run_backend_invoke_artifact_only_verify(args: argparse.Namespace) -> int:
    """pcae backend invoke artifact-only verify --latest [--json]

    Verifies the latest assessment digest integrity.
    """
    assessment = load_latest_artifact_only_invocation_command_boundary_assessment()
    if assessment is None:
        return _abort("No latest assessment found. Run a dry-run first.", args)

    v = verify_artifact_only_invocation_command_boundary_assessment(assessment)
    if getattr(args, "json", False):
        print(json.dumps(v, indent=2))
    else:
        if v["valid"]:
            print(f"Assessment {assessment.assessment_id}: valid ✅")
        else:
            print(f"Assessment {assessment.assessment_id}: INVALID ❌")
            for issue in v.get("issues", []):
                print(f"  - {issue}")
    return 0 if v["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95P — Evidence chain bundle dry-run CLI
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ArtifactOnlyInvocationEvidenceChainBundle,
    ArtifactOnlyInvocationEvidenceChainBundleAssessment,
    validate_artifact_only_invocation_evidence_chain_bundle,
    verify_evidence_chain_bundle,
    persist_evidence_chain_bundle_assessment,
    verify_evidence_chain_bundle_assessment,
    load_latest_evidence_chain_bundle_assessment,
)


def _load_bundle(path: str, args: argparse.Namespace) -> tuple:
    from pathlib import Path as _P
    p = _P(path)
    if not p.is_file():
        msg = f"Bundle is a directory: {path}" if p.is_dir() else f"Bundle file not found: {path}"
        if getattr(args, "json", False):
            print(json.dumps({"error": msg}))
        else:
            print(f"Error: {msg}")
        return None, 1
    try:
        data = json.loads(p.read_text())
        bundle = ArtifactOnlyInvocationEvidenceChainBundle.from_dict(data)
    except Exception as exc:
        msg = f"Failed to load bundle: {exc}"
        if getattr(args, "json", False):
            print(json.dumps({"error": msg}))
        else:
            print(f"Error: {msg}")
        return None, 1
    if bundle.record_digest:
        v = verify_evidence_chain_bundle(bundle)
        if not v["valid"]:
            msg = f"Bundle verification failed: {v['issues']}"
            if getattr(args, "json", False):
                print(json.dumps({"error": msg}))
            else:
                print(f"Error: {msg}")
            return None, 1
    return bundle, 0


def _print_bundle_assessment_text(a: ArtifactOnlyInvocationEvidenceChainBundleAssessment) -> None:
    print(f"Bundle Assessment: {a.assessment_id}")
    print(f"  Decision:          {a.decision}")
    print(f"  Ready:             {'yes' if a.ready else 'no'}")
    if a.hard_blocks:
        print(f"  Hard blocks:       {', '.join(a.hard_blocks)}")
    if a.missing_artifacts:
        print(f"  Missing artifacts: {', '.join(a.missing_artifacts)}")
    print(f"  Evidence chain:    {'ready' if a.evidence_chain_ready else 'incomplete'}")
    print(f"  Broker/shell-gate: {'ready' if a.broker_shell_gate_ready else 'not ready'}")
    print(f"  Execution allowed: {'yes' if a.execution_allowed else 'no'}")
    print(f"  Execute supported: {'yes' if a.execute_supported else 'no'}")
    print(f"  Dry-run only:      {'yes' if a.dry_run_only else 'no'}")
    print(f"  Subprocess:        {'yes' if not a.no_subprocess else 'no'}")
    print(f"  Network:           {'yes' if not a.no_network else 'no'}")
    print(f"  Repo mutation:     {'yes' if not a.no_repo_mutation else 'no'}")
    print(f"  Apply:             {'yes' if not a.no_apply else 'no'}")
    print()
    print("  ⚠️  Dry-run only. No backend was invoked.")


def run_backend_invoke_artifact_only_bundle_dry_run(args: argparse.Namespace) -> int:
    bundle_path = getattr(args, "bundle", "") or ""
    save = getattr(args, "save", False) or False
    if not bundle_path:
        msg = "Missing --bundle <path>"
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    bundle, code = _load_bundle(bundle_path, args)
    if bundle is None:
        return code
    a = validate_artifact_only_invocation_evidence_chain_bundle(bundle)
    if save:
        persist_evidence_chain_bundle_assessment(a)
    if getattr(args, "json", False):
        print(json.dumps(a.to_dict(), indent=2))
    else:
        _print_bundle_assessment_text(a)
    return 0


def run_backend_invoke_artifact_only_bundle_show(args: argparse.Namespace) -> int:
    a = load_latest_evidence_chain_bundle_assessment()
    if a is None:
        msg = "No latest bundle assessment found. Run a dry-run first."
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    if getattr(args, "json", False):
        print(json.dumps(a.to_dict(), indent=2))
    else:
        _print_bundle_assessment_text(a)
    return 0


def run_backend_invoke_artifact_only_bundle_verify(args: argparse.Namespace) -> int:
    a = load_latest_evidence_chain_bundle_assessment()
    if a is None:
        msg = "No latest bundle assessment found."
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    v = verify_evidence_chain_bundle_assessment(a)
    if getattr(args, "json", False):
        print(json.dumps(v, indent=2))
    else:
        print(f"Assessment {a.assessment_id}: {'valid ✅' if v['valid'] else 'INVALID ❌'}")
        for issue in v.get("issues", []):
            print(f"  - {issue}")
    return 0 if v["valid"] else 1


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95Q — Evidence chain bundle end-to-end dry-run demo
# ═══════════════════════════════════════════════════════════════════════════

def run_backend_invoke_artifact_only_bundle_demo(args: argparse.Namespace) -> int:
    """pcae backend invoke artifact-only bundle demo [--save] [--json]

    End-to-end dry-run demo: valid fixture → bundle → validate → assessment.
    Never executes anything.
    """
    from tests.artifact_only_invocation_fixtures import build_valid_boundary
    from pcae.core.backend_invocations import (
        ArtifactOnlyInvocationEvidenceChainBundle,
        validate_artifact_only_invocation_evidence_chain_bundle,
        persist_evidence_chain_bundle_assessment,
        DECISION_ALLOW_DRY_RUN,
        COMMAND_MODE_DRY_RUN,
    )
    import uuid

    save = getattr(args, "save", False) or False

    # Build valid fixture chain
    boundary = build_valid_boundary()

    # Construct bundle from fixture
    bundle = ArtifactOnlyInvocationEvidenceChainBundle(
        bundle_id=f"eb-demo-{uuid.uuid4().hex[:8]}",
        phase_id="95Q", task_id="demo",
        backend_id=boundary.backend_id,
        adapter_id=boundary.adapter_id,
        prompt_artifact_path=boundary.prompt_artifact_path,
        prompt_artifact_digest=boundary.prompt_artifact_digest,
        preflight_artifact_path=boundary.preflight_artifact_path,
        preflight_artifact_digest=boundary.preflight_artifact_digest,
        runtime_evidence_path=boundary.runtime_evidence_path,
        runtime_evidence_digest=boundary.runtime_evidence_digest,
        approval_artifact_path=boundary.approval_artifact_path,
        approval_artifact_digest=boundary.approval_artifact_digest,
        invocation_plan_path=boundary.invocation_plan_path,
        invocation_plan_digest=boundary.invocation_plan_digest,
        broker_decision_id=boundary.broker_decision_id,
        broker_decision=boundary.broker_decision,
        shell_gate_decision_id=boundary.shell_gate_decision_id,
        shell_gate_decision=boundary.shell_gate_decision,
        command_boundary_path="/demo/cb.json",
        command_boundary_digest="sha256:demo",
        command_boundary_assessment_path="/demo/cba.json",
        command_boundary_assessment_digest="sha256:demo-assessment",
        output_quarantine_path=boundary.output_quarantine_path,
        audit_path=boundary.audit_path,
        timeout_seconds=boundary.timeout_seconds,
        redaction_policy_id=boundary.redaction_policy_id,
        operator_approval_reference=boundary.operator_approval_reference,
        command_mode=COMMAND_MODE_DRY_RUN,
    )
    bundle.record_digest = bundle.compute_digest()

    assessment = validate_artifact_only_invocation_evidence_chain_bundle(bundle)

    if save:
        persist_evidence_chain_bundle_assessment(assessment)

    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps({
            "demo_only": True,
            "dry_run_only": True,
            "execution_allowed": False,
            "execute_supported": False,
            "real_backend_invoked": False,
            "adapter_executed": False,
            "subprocess": False,
            "shell_command": False,
            "network": False,
            "repo_mutation": False,
            "apply": False,
            "patch_parsing": False,
            "commit_push_authorized": False,
            "telegram_inbound": False,
            "bundle_ready": assessment.ready,
            "assessment_ready": assessment.ready,
            "decision": assessment.decision,
            "assessment": assessment.to_dict(),
        }, indent=2))
    else:
        print("Evidence Chain Bundle End-to-End Dry-Run Demo")
        print(f"  Demo only:          yes")
        print(f"  Dry-run only:       yes")
        print(f"  Bundle ready:       {'yes' if assessment.ready else 'no'}")
        print(f"  Decision:           {assessment.decision}")
        print(f"  Execution allowed:  {'yes' if assessment.execution_allowed else 'no'}")
        print(f"  Execute supported:  {'yes' if assessment.execute_supported else 'no'}")
        print(f"  Real backend:       {'yes' if not assessment.no_real_backend_invoked else 'no'}")
        print(f"  Adapter executed:   {'yes' if not assessment.no_adapter_executed else 'no'}")
        print(f"  Subprocess:         {'yes' if not assessment.no_subprocess else 'no'}")
        print(f"  Shell command:      no")
        print(f"  Network:            {'yes' if not assessment.no_network else 'no'}")
        print(f"  Repo mutation:      {'yes' if not assessment.no_repo_mutation else 'no'}")
        print(f"  Apply:              {'yes' if not assessment.no_apply else 'no'}")
        print(f"  Patch parsing:      {'yes' if not assessment.no_patch_parsing else 'no'}")
        print(f"  Commit/push auth:   {'yes' if not assessment.no_commit_push_authorization else 'no'}")
        print(f"  Telegram inbound:   {'yes' if not assessment.no_telegram_inbound else 'no'}")
        print()
        print("  ⚠️  Demo only. No backend was invoked. No adapter was executed.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Phase 95T — Artifact-only dry-run orchestration CLI
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.backend_invocations import (
    ArtifactOnlyDryRunOrchestrationPlan,
    ArtifactOnlyDryRunOrchestrationAssessment,
    validate_artifact_only_dry_run_orchestration_plan,
    verify_orchestration_plan,
    persist_orchestration_assessment,
    verify_orchestration_assessment,
)


def _load_orch_plan(path: str, args: argparse.Namespace) -> tuple:
    from pathlib import Path as _P
    p = _P(path)
    if not p.is_file():
        msg = f"Plan is a directory: {path}" if p.is_dir() else f"Plan file not found: {path}"
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return None, 1
    try:
        data = json.loads(p.read_text())
        plan = ArtifactOnlyDryRunOrchestrationPlan.from_dict(data)
    except Exception as exc:
        msg = f"Failed to load plan: {exc}"
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return None, 1
    if plan.record_digest:
        v = verify_orchestration_plan(plan)
        if not v["valid"]:
            msg = f"Plan verification failed: {v['issues']}"
            print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
            return None, 1
    return plan, 0


def _load_latest_orch_assessment() -> ArtifactOnlyDryRunOrchestrationAssessment | None:
    from pcae.core.backend_invocations import _orch_dir
    lp = _orch_dir() / "assessments" / "latest-assessment.json"
    if not lp.exists():
        return None
    try:
        data = json.loads(lp.read_text())
        return ArtifactOnlyDryRunOrchestrationAssessment.from_dict(data)
    except Exception:
        return None


def _print_orch_assessment_text(a: ArtifactOnlyDryRunOrchestrationAssessment) -> None:
    print(f"Orchestration Assessment: {a.assessment_id}")
    print(f"  Decision:            {a.decision}")
    print(f"  Ready:               {'yes' if a.ready else 'no'}")
    if a.cumulative_hard_blocks:
        print(f"  Hard blocks:         {', '.join(a.cumulative_hard_blocks)}")
    print(f"  Step results:        {len(a.step_results)} step(s)")
    for sr in a.step_results:
        status = "ready" if sr.ready else "blocked"
        print(f"    {sr.step_order}: {sr.step_name} — {status}")
    print(f"  Execution allowed:   {'yes' if a.execution_allowed else 'no'}")
    print(f"  Execute supported:   {'yes' if a.execute_supported else 'no'}")
    print(f"  Dry-run only:        {'yes' if a.dry_run_only else 'no'}")
    print(f"  Real backend:        {'yes' if not a.no_real_backend_invoked else 'no'}")
    print(f"  Adapter executed:    {'yes' if not a.no_adapter_executed else 'no'}")
    print(f"  Subprocess:          {'yes' if not a.no_subprocess else 'no'}")
    print(f"  Network:             {'yes' if not a.no_network else 'no'}")
    print(f"  Repo mutation:       {'yes' if not a.no_repo_mutation else 'no'}")
    print(f"  Apply:               {'yes' if not a.no_apply else 'no'}")
    print(f"  Patch parsing:       {'yes' if not a.no_patch_parsing else 'no'}")
    print(f"  Commit/push auth:    {'yes' if not a.no_commit_push_authorization else 'no'}")
    print(f"  Telegram inbound:    {'yes' if not a.no_telegram_inbound else 'no'}")
    print()
    print("  ⚠️  Dry-run only. No backend was invoked.")


def run_backend_invoke_artifact_only_orch_dry_run(args: argparse.Namespace) -> int:
    plan_path = getattr(args, "plan", "") or ""
    save = getattr(args, "save", False) or False
    if not plan_path:
        msg = "Missing --plan <path>"
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    plan, code = _load_orch_plan(plan_path, args)
    if plan is None:
        return code
    a = validate_artifact_only_dry_run_orchestration_plan(plan)
    if save:
        persist_orchestration_assessment(a)
    if getattr(args, "json", False):
        print(json.dumps(a.to_dict(), indent=2))
    else:
        _print_orch_assessment_text(a)
    return 0


def run_backend_invoke_artifact_only_orch_show(args: argparse.Namespace) -> int:
    a = _load_latest_orch_assessment()
    if a is None:
        msg = "No latest orchestration assessment found."
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    if getattr(args, "json", False):
        print(json.dumps(a.to_dict(), indent=2))
    else:
        _print_orch_assessment_text(a)
    return 0


def run_backend_invoke_artifact_only_orch_verify(args: argparse.Namespace) -> int:
    a = _load_latest_orch_assessment()
    if a is None:
        msg = "No latest orchestration assessment found."
        print(json.dumps({"error": msg}) if getattr(args, "json", False) else f"Error: {msg}")
        return 1
    v = verify_orchestration_assessment(a)
    if getattr(args, "json", False):
        print(json.dumps(v, indent=2))
    else:
        print(f"Assessment {a.assessment_id}: {'valid ✅' if v['valid'] else 'INVALID ❌'}")
        for issue in v.get("issues", []):
            print(f"  - {issue}")
    return 0 if v["valid"] else 1
