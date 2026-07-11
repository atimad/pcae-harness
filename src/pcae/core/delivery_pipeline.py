"""Phase 134E.6: Delivery Pipeline Generalization.

Implements a deterministic, transport-neutral Delivery Pipeline that
accepts a verified ``RenderingResult`` (134E.5, independently verified
and repaired by 134E.5V) and prepares or executes delivery through
explicitly registered delivery adapters, without changing the rendered
engineering content.

**This module is not yet active lifecycle authority.** Nothing in the
current governed reporting/finalization/notification path imports or
calls into this module. The current production Telegram delivery,
``pcae phase complete``, and PFN-001 dispatch remain entirely
unaffected and unchanged.

Architectural position (preserved, not merged):

    Canonical Engineering Evidence
            |
            v
    Evidence Extraction
            |
            v
    Derived Evidence Views
            |
            v
    RenderingResult
            |
            v
    Delivery Pipeline                    <- this module
            |
            v
    Delivery Adapter
            |
            v
    Adapter Delivery Outcome
            |
            v
    External Delivery Receipt Model      (134E.7, not implemented)

The Delivery Pipeline consumes only a validated ``RenderingResult`` --
it never imports the canonical evidence model, the extraction layer,
or either derived-view composition module beneath it. It reuses the
existing, already-verified external-delivery authorization gate from
``pcae.core.notifications`` (``_external_delivery_authorized``) rather
than duplicating it, per this phase's own explicit instruction to
reuse the channel-agnostic authorization boundary 134B.1/134B.2
established.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from pcae.core.notifications import _external_delivery_authorized
from pcae.core.rendering import RenderingResult


# ═══════════════════════════════════════════════════════════════════════
# Vocabulary
# ═══════════════════════════════════════════════════════════════════════


class DeliveryPurpose(str, Enum):
    """The set of delivery purposes required by current Track 134
    design -- deliberately not a broad arbitrary messaging platform.
    """

    OPERATOR_TERMINAL_REPORT = "operator_terminal_report"
    CANONICAL_PHASE_REPORT = "canonical_phase_report"
    CORRECTION_NOTICE = "correction_notice"
    LIVE_INTEGRATION_TEST = "live_integration_test"
    MILESTONE_DELIVERY = "milestone_delivery"


class DestinationClassification(str, Enum):
    """Safe destination *classification* -- never a concrete channel
    ID, email address, or webhook URL. Concrete destinations remain
    inside adapter configuration, resolved via the existing neutral
    configuration boundary, never serialized here.
    """

    PRODUCTION_OPERATOR = "production_operator"
    INTEGRATION_TEST = "integration_test"
    SYNTHETIC_RECORDING = "synthetic_recording"
    DISABLED = "disabled"
    FUTURE_GOVERNED = "future_governed"


class DeliveryMode(str, Enum):
    """Transport-neutral delivery modes. ``OVERVIEW_PLUS_ATTACHMENT``
    is reserved but never selected by this phase's mode-selection
    algorithm -- composing a governed overview artifact is explicitly
    out of scope (Section "Content Packaging" of this phase's own
    brief: an overview must already exist as a verified rendered
    artifact or be produced by an explicitly governed renderer, neither
    of which this phase introduces).
    """

    INLINE = "inline"
    ATTACHMENT = "attachment"
    MULTIPART_INLINE = "multipart_inline"
    OVERVIEW_PLUS_ATTACHMENT = "overview_plus_attachment"
    DISABLED = "disabled"


class DeliveryOutcome(str, Enum):
    DELIVERED = "delivered"
    FAILED = "failed"
    PARTIALLY_DELIVERED = "partially_delivered"
    DISABLED_BY_POLICY = "disabled_by_policy"
    BLOCKED_BY_AUTHORIZATION = "blocked_by_authorization"
    INVALID_PLAN = "invalid_plan"
    UNSUPPORTED = "unsupported"


class RetryRecommendation(str, Enum):
    RETRY_RECOMMENDED = "retry_recommended"
    RETRY_NOT_RECOMMENDED = "retry_not_recommended"
    NOT_APPLICABLE = "not_applicable"


#: Deterministic filename extension per rendering media type -- used
#: only for attachment unit naming, never for content interpretation.
_EXTENSION_FOR_MEDIA_TYPE: dict[str, str] = {
    "text/markdown": "md",
    "text/plain": "txt",
    "application/json": "json",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    blocking: bool

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "blocking": self.blocking}


# ═══════════════════════════════════════════════════════════════════════
# Logical delivery identity
# ═══════════════════════════════════════════════════════════════════════


def compute_logical_delivery_id(
    phase_id: str, rendering_digest: str, purpose: DeliveryPurpose,
    destination: DestinationClassification, adapter_id: str, policy_version: str,
) -> str:
    """Deterministic logical delivery identity derived solely from
    governed inputs. Never includes a random UUID, attempt number,
    retry timestamp, process identity, model identity, or transport
    response ID. Because ``rendering_digest`` is one of the inputs, a
    changed rendering under otherwise-identical governed inputs always
    produces a *different* logical delivery identity by construction --
    "changed content under the same logical identity" is structurally
    unreachable, not merely checked after the fact.

    134E.6V finding (BLOCKING, repaired): the original implementation
    joined the six input fields with a bare ``"|"`` separator before
    hashing. Because ``phase_id``, ``adapter_id``, and
    ``policy_version`` are unrestricted free-text strings (nothing
    prevents an adapter from being registered under an ``adapter_id``
    containing ``"|"``), this was reproducibly ambiguous at field
    boundaries: two *semantically different* input tuples -- e.g.
    ``phase_id="X|Y", adapter_id="adapterZ"`` versus
    ``phase_id="X", rendering_digest="Y|<real-digest>", adapter_id=
    "adapterZ"`` -- could hash to the identical logical delivery
    identity, confirmed via direct reproduction before any test was
    written. Repaired by hashing an unambiguous canonical JSON array of
    the six fields instead of a delimiter-joined string; JSON's own
    string escaping makes every field boundary structurally
    unambiguous regardless of field content.
    """
    payload = json.dumps(
        [phase_id, rendering_digest, purpose.value, destination.value, adapter_id, policy_version],
        sort_keys=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Delivery request
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryRequest:
    """The deterministic input to delivery planning. Contains no
    secrets, credentials, or concrete destination values -- those
    belong to adapter configuration, resolved through the existing
    neutral configuration boundary, never serialized here.
    """

    logical_delivery_id: str
    phase_id: str
    rendering_view_id: str
    rendering_digest: str
    renderer_id: str
    renderer_version: str
    media_type: str
    rendered_content: str
    content_size: int
    destination_classification: DestinationClassification
    adapter_id: str
    adapter_version: str
    delivery_purpose: DeliveryPurpose
    is_synthetic: bool
    requested_mode: DeliveryMode | None
    policy_version: str
    has_uncertainty: bool
    has_limitations: bool
    diagnostics: tuple[Diagnostic, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_delivery_id": self.logical_delivery_id,
            "phase_id": self.phase_id,
            "rendering_view_id": self.rendering_view_id,
            "rendering_digest": self.rendering_digest,
            "renderer_id": self.renderer_id,
            "renderer_version": self.renderer_version,
            "media_type": self.media_type,
            "rendered_content": self.rendered_content,
            "content_size": self.content_size,
            "destination_classification": self.destination_classification.value,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "delivery_purpose": self.delivery_purpose.value,
            "is_synthetic": self.is_synthetic,
            "requested_mode": self.requested_mode.value if self.requested_mode else None,
            "policy_version": self.policy_version,
            "has_uncertainty": self.has_uncertainty,
            "has_limitations": self.has_limitations,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


def build_delivery_request(
    result: RenderingResult, *, adapter_id: str, adapter_version: str,
    destination: DestinationClassification, purpose: DeliveryPurpose,
    policy_version: str, is_synthetic: bool = True,
    requested_mode: DeliveryMode | None = None,
) -> DeliveryRequest:
    """Build a deterministic ``DeliveryRequest`` from a verified
    ``RenderingResult``. Fail-closed for an empty/invalid rendering.
    """
    if not result.rendered_content.strip():
        raise ValueError("Cannot build a delivery request from an empty rendering")
    if not result.source_evidence_id:
        raise ValueError("RenderingResult.source_evidence_id must be non-empty")

    rendering_digest = result.compute_digest()
    phase_id = result.source_evidence_id.split("#", 1)[0]
    logical_id = compute_logical_delivery_id(
        phase_id, rendering_digest, purpose, destination, adapter_id, policy_version,
    )
    # RenderingResult carries a single `limitations` list (it does not
    # separately distinguish "uncertainty" from "limitations" the way
    # the composed views do) -- both indicator fields are derived from
    # it, the only signal available at this layer.
    has_limitations = bool(result.limitations)
    return DeliveryRequest(
        logical_delivery_id=logical_id,
        phase_id=phase_id,
        rendering_view_id=result.source_view_id,
        rendering_digest=rendering_digest,
        renderer_id=result.renderer_id,
        renderer_version=result.renderer_version,
        media_type=result.media_type,
        rendered_content=result.rendered_content,
        content_size=len(result.rendered_content.encode("utf-8")),
        destination_classification=destination,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        delivery_purpose=purpose,
        is_synthetic=is_synthetic,
        requested_mode=requested_mode,
        policy_version=policy_version,
        has_uncertainty=has_limitations,
        has_limitations=has_limitations,
        diagnostics=(),
    )


# ═══════════════════════════════════════════════════════════════════════
# Adapter contract and registry
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class AdapterCapabilities:
    adapter_id: str
    adapter_version: str
    supported_media_types: frozenset[str]
    supported_modes: frozenset[DeliveryMode]
    max_inline_bytes: int
    supports_attachment: bool
    represents_external_delivery: bool
    safe_destination_alias: str
    always_disabled: bool = False

    def __post_init__(self) -> None:
        if not self.adapter_id:
            raise ValueError("AdapterCapabilities.adapter_id must be non-empty")
        if not self.adapter_version:
            raise ValueError("AdapterCapabilities.adapter_version must be non-empty")
        object.__setattr__(self, "supported_media_types", frozenset(self.supported_media_types))
        object.__setattr__(self, "supported_modes", frozenset(self.supported_modes))


AdapterDeliverFn = Callable[["DeliveryUnit"], "AdapterUnitOutcome"]


@dataclass(frozen=True)
class DeliveryAdapter:
    capabilities: AdapterCapabilities
    deliver_fn: AdapterDeliverFn


_ADAPTER_REGISTRY: dict[str, DeliveryAdapter] = {}


def register_adapter(adapter: DeliveryAdapter) -> None:
    """Register a delivery adapter. Fail-closed against silent
    overwrite, mirroring the identical convention the extraction
    profile registry and ``rendering.register_renderer()`` already
    established: a differing re-registration under an existing
    ``adapter_id`` raises; an identical re-registration is a harmless
    no-op.
    """
    existing = _ADAPTER_REGISTRY.get(adapter.capabilities.adapter_id)
    if existing is not None and (
        existing.capabilities != adapter.capabilities
        or existing.deliver_fn is not adapter.deliver_fn
    ):
        raise ValueError(
            f"Adapter {adapter.capabilities.adapter_id!r} is already registered "
            f"(version {existing.capabilities.adapter_version!r}); refusing to "
            "silently overwrite with a different adapter. Register under a new "
            "adapter_id instead."
        )
    _ADAPTER_REGISTRY[adapter.capabilities.adapter_id] = adapter


def get_adapter(adapter_id: str) -> DeliveryAdapter:
    if adapter_id not in _ADAPTER_REGISTRY:
        raise ValueError(f"Unsupported adapter: {adapter_id!r}")
    return _ADAPTER_REGISTRY[adapter_id]


# ═══════════════════════════════════════════════════════════════════════
# Delivery unit and outcome
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryUnit:
    unit_id: str
    index: int
    total: int
    unit_kind: str
    content: str
    content_hash: str
    media_type: str
    filename: str | None
    logical_delivery_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id, "index": self.index, "total": self.total,
            "unit_kind": self.unit_kind, "content": self.content,
            "content_hash": self.content_hash, "media_type": self.media_type,
            "filename": self.filename, "logical_delivery_id": self.logical_delivery_id,
        }


@dataclass(frozen=True)
class AdapterUnitOutcome:
    unit_id: str
    delivered: bool
    retryable: bool
    adapter_response_ref: str | None
    diagnostic: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id, "delivered": self.delivered,
            "retryable": self.retryable, "adapter_response_ref": self.adapter_response_ref,
            "diagnostic": self.diagnostic,
        }


# ═══════════════════════════════════════════════════════════════════════
# Delivery policy
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryPolicy:
    policy_version: str
    inline_size_threshold: int
    allow_attachment: bool
    allow_multipart: bool
    allow_overview_plus_attachment: bool

    def __post_init__(self) -> None:
        if not self.policy_version:
            raise ValueError("DeliveryPolicy.policy_version must be non-empty")
        if self.inline_size_threshold <= 0:
            raise ValueError("DeliveryPolicy.inline_size_threshold must be positive")


DEFAULT_POLICY = DeliveryPolicy(
    policy_version="1.0", inline_size_threshold=8000,
    allow_attachment=True, allow_multipart=True, allow_overview_plus_attachment=False,
)


# ═══════════════════════════════════════════════════════════════════════
# Deterministic segmentation
# ═══════════════════════════════════════════════════════════════════════


def _segment_content(content: str, max_bytes: int) -> list[str]:
    """Deterministic, lossless segmentation on character offsets.
    ``"".join(segments) == content`` always holds exactly. Splits at
    the last newline before the byte threshold where one exists, never
    mid-line except when a single line itself exceeds ``max_bytes``
    (unavoidable, still fully deterministic).
    """
    segments: list[str] = []
    start = 0
    encoded_len = len(content.encode("utf-8"))
    if encoded_len <= max_bytes:
        return [content]
    n = len(content)
    while start < n:
        # Binary-search-free approximation: walk by characters, tracking
        # byte length, since PCAE content is predominantly ASCII/UTF-8
        # text and correctness (not micro-performance) is what matters.
        end = start
        byte_count = 0
        last_newline = -1
        while end < n and byte_count < max_bytes:
            ch = content[end]
            byte_count += len(ch.encode("utf-8"))
            if ch == "\n":
                last_newline = end
            end += 1
        if end < n and last_newline > start:
            end = last_newline + 1
        segments.append(content[start:end])
        start = end
    return segments


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _filename_for(logical_delivery_id: str, media_type: str) -> str:
    ext = _EXTENSION_FOR_MEDIA_TYPE.get(media_type, "bin")
    return f"{logical_delivery_id[:16]}.{ext}"


# ═══════════════════════════════════════════════════════════════════════
# Delivery plan
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryPlan:
    logical_delivery_id: str
    adapter_id: str
    adapter_version: str
    destination_classification: DestinationClassification
    selected_mode: DeliveryMode
    units: tuple[DeliveryUnit, ...]
    policy_version: str
    content_preserved: bool
    diagnostics: tuple[Diagnostic, ...]
    rendering_view_id: str
    rendering_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "units", tuple(self.units))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_delivery_id": self.logical_delivery_id,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "destination_classification": self.destination_classification.value,
            "selected_mode": self.selected_mode.value,
            "units": [u.to_dict() for u in self.units],
            "policy_version": self.policy_version,
            "content_preserved": self.content_preserved,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "rendering_view_id": self.rendering_view_id,
            "rendering_digest": self.rendering_digest,
        }


def _select_mode(
    content_size: int, requested_mode: DeliveryMode | None,
    caps: AdapterCapabilities, policy: DeliveryPolicy,
) -> DeliveryMode:
    if requested_mode is not None:
        if requested_mode not in caps.supported_modes:
            raise ValueError(
                f"Requested delivery mode {requested_mode.value!r} is not supported "
                f"by adapter {caps.adapter_id!r}"
            )
        return requested_mode

    inline_limit = min(policy.inline_size_threshold, caps.max_inline_bytes)
    if content_size <= inline_limit and DeliveryMode.INLINE in caps.supported_modes:
        return DeliveryMode.INLINE
    if (
        policy.allow_attachment and caps.supports_attachment
        and DeliveryMode.ATTACHMENT in caps.supported_modes
    ):
        return DeliveryMode.ATTACHMENT
    if policy.allow_multipart and DeliveryMode.MULTIPART_INLINE in caps.supported_modes:
        return DeliveryMode.MULTIPART_INLINE
    raise ValueError(
        f"No complete delivery mode available for adapter {caps.adapter_id!r} "
        f"and content size {content_size} bytes"
    )


def plan_delivery(
    request: DeliveryRequest, *, policy: DeliveryPolicy = DEFAULT_POLICY,
) -> DeliveryPlan:
    """Build a deterministic ``DeliveryPlan`` from a ``DeliveryRequest``.

    Fail-closed for: unknown adapter, incompatible media type,
    unsupported requested mode, and "no complete delivery mode
    available" (never truncates or falls back to a status-only
    message). Never raises for an ordinary successful plan -- planning
    always either produces a plan that fully represents
    ``request.rendered_content`` or raises.
    """
    adapter = get_adapter(request.adapter_id)
    caps = adapter.capabilities

    if request.media_type not in caps.supported_media_types:
        raise ValueError(
            f"Adapter {caps.adapter_id!r} does not support media type "
            f"{request.media_type!r}"
        )

    if caps.always_disabled:
        # An always-disabled adapter never attempts delivery regardless
        # of content size, so ordinary mode-selection (which exists to
        # find a transport-compatible packaging) does not apply -- it
        # would otherwise spuriously fail closed on "no complete mode
        # available" for content that will never actually be sent. The
        # full content is still recorded on a single DISABLED-mode unit
        # so content_preserved remains an honest, non-strengthened
        # signal (content is not lost, only never delivered).
        content = request.rendered_content
        unit = DeliveryUnit(
            unit_id=f"{request.logical_delivery_id}:0:1", index=0, total=1,
            unit_kind="inline", content=content, content_hash=_content_hash(content),
            media_type=request.media_type, filename=None,
            logical_delivery_id=request.logical_delivery_id,
        )
        return DeliveryPlan(
            logical_delivery_id=request.logical_delivery_id, adapter_id=request.adapter_id,
            adapter_version=request.adapter_version,
            destination_classification=request.destination_classification,
            selected_mode=DeliveryMode.DISABLED, units=(unit,),
            policy_version=policy.policy_version, content_preserved=True,
            diagnostics=(), rendering_view_id=request.rendering_view_id,
            rendering_digest=request.rendering_digest,
        )

    mode = _select_mode(request.content_size, request.requested_mode, caps, policy)

    units: list[DeliveryUnit] = []
    if mode == DeliveryMode.INLINE:
        content = request.rendered_content
        units.append(DeliveryUnit(
            unit_id=f"{request.logical_delivery_id}:0:1", index=0, total=1,
            unit_kind="inline", content=content, content_hash=_content_hash(content),
            media_type=request.media_type, filename=None,
            logical_delivery_id=request.logical_delivery_id,
        ))
    elif mode == DeliveryMode.ATTACHMENT:
        content = request.rendered_content
        filename = _filename_for(request.logical_delivery_id, request.media_type)
        units.append(DeliveryUnit(
            unit_id=f"{request.logical_delivery_id}:0:1", index=0, total=1,
            unit_kind="attachment", content=content, content_hash=_content_hash(content),
            media_type=request.media_type, filename=filename,
            logical_delivery_id=request.logical_delivery_id,
        ))
    elif mode == DeliveryMode.MULTIPART_INLINE:
        segments = _segment_content(request.rendered_content, min(policy.inline_size_threshold, caps.max_inline_bytes))
        total = len(segments)
        for i, segment in enumerate(segments):
            units.append(DeliveryUnit(
                unit_id=f"{request.logical_delivery_id}:{i}:{total}", index=i, total=total,
                unit_kind="inline", content=segment, content_hash=_content_hash(segment),
                media_type=request.media_type, filename=None,
                logical_delivery_id=request.logical_delivery_id,
            ))
    else:  # pragma: no cover — _select_mode never returns DISABLED/OVERVIEW_PLUS_ATTACHMENT
        raise ValueError(f"Unsupported selected mode: {mode.value!r}")

    reconstructed = "".join(u.content for u in units)
    content_preserved = reconstructed == request.rendered_content
    diagnostics: list[Diagnostic] = []
    if not content_preserved:
        diagnostics.append(Diagnostic(
            code="content_preservation_failure",
            message="reconstructed unit content does not match rendered_content",
            blocking=True,
        ))
        raise ValueError("Delivery plan content-preservation check failed")

    return DeliveryPlan(
        logical_delivery_id=request.logical_delivery_id,
        adapter_id=request.adapter_id,
        adapter_version=request.adapter_version,
        destination_classification=request.destination_classification,
        selected_mode=mode,
        units=tuple(units),
        policy_version=policy.policy_version,
        content_preserved=content_preserved,
        diagnostics=tuple(diagnostics),
        rendering_view_id=request.rendering_view_id,
        rendering_digest=request.rendering_digest,
    )


# ═══════════════════════════════════════════════════════════════════════
# Delivery execution
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DeliveryExecutionResult:
    logical_delivery_id: str
    adapter_id: str
    adapter_version: str
    destination_classification: DestinationClassification
    selected_mode: DeliveryMode
    requested_unit_count: int
    attempted_unit_count: int
    delivered_unit_count: int
    failed_unit_count: int
    unit_outcomes: tuple[AdapterUnitOutcome, ...]
    overall_outcome: DeliveryOutcome
    partial: bool
    retry_recommendation: RetryRecommendation
    diagnostics: tuple[Diagnostic, ...]
    rendering_view_id: str
    rendering_digest: str
    policy_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "unit_outcomes", tuple(self.unit_outcomes))
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_delivery_id": self.logical_delivery_id,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "destination_classification": self.destination_classification.value,
            "selected_mode": self.selected_mode.value,
            "requested_unit_count": self.requested_unit_count,
            "attempted_unit_count": self.attempted_unit_count,
            "delivered_unit_count": self.delivered_unit_count,
            "failed_unit_count": self.failed_unit_count,
            "unit_outcomes": [o.to_dict() for o in self.unit_outcomes],
            "overall_outcome": self.overall_outcome.value,
            "partial": self.partial,
            "retry_recommendation": self.retry_recommendation.value,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "rendering_view_id": self.rendering_view_id,
            "rendering_digest": self.rendering_digest,
            "policy_version": self.policy_version,
        }


def execute_delivery(
    plan: DeliveryPlan, *, authorized: bool | None = None,
) -> DeliveryExecutionResult:
    """Execute a valid ``DeliveryPlan`` against its registered adapter.

    ``authorized`` overrides the live authorization check (used only by
    tests exercising the authorization boundary deterministically);
    when omitted, the real, already-governed
    ``pcae.core.notifications._external_delivery_authorized()`` gate is
    consulted for any adapter whose capabilities declare
    ``represents_external_delivery=True``. Adapters not marked as
    external (recording/null) never consult authorization at all,
    matching the identical fail-closed-by-classification posture
    ``notifications.py`` already established.

    Never mutates ``plan``; never regenerates the plan; always
    preserves the plan's own ``logical_delivery_id``.
    """
    adapter = get_adapter(plan.adapter_id)
    caps = adapter.capabilities

    if caps.always_disabled:
        return DeliveryExecutionResult(
            logical_delivery_id=plan.logical_delivery_id, adapter_id=plan.adapter_id,
            adapter_version=plan.adapter_version,
            destination_classification=plan.destination_classification,
            selected_mode=plan.selected_mode, requested_unit_count=len(plan.units),
            attempted_unit_count=0, delivered_unit_count=0, failed_unit_count=0,
            unit_outcomes=(), overall_outcome=DeliveryOutcome.DISABLED_BY_POLICY,
            partial=False, retry_recommendation=RetryRecommendation.NOT_APPLICABLE,
            diagnostics=(Diagnostic(
                code="disabled_adapter", message="adapter is always-disabled by policy",
                blocking=False,
            ),),
            rendering_view_id=plan.rendering_view_id, rendering_digest=plan.rendering_digest,
            policy_version=plan.policy_version,
        )

    if caps.represents_external_delivery:
        auth = authorized if authorized is not None else _external_delivery_authorized()
        if not auth:
            return DeliveryExecutionResult(
                logical_delivery_id=plan.logical_delivery_id, adapter_id=plan.adapter_id,
                adapter_version=plan.adapter_version,
                destination_classification=plan.destination_classification,
                selected_mode=plan.selected_mode, requested_unit_count=len(plan.units),
                attempted_unit_count=0, delivered_unit_count=0, failed_unit_count=0,
                unit_outcomes=(), overall_outcome=DeliveryOutcome.BLOCKED_BY_AUTHORIZATION,
                partial=False, retry_recommendation=RetryRecommendation.NOT_APPLICABLE,
                diagnostics=(Diagnostic(
                    code="external_delivery_unauthorized",
                    message="external delivery requires explicit governed authorization",
                    blocking=True,
                ),),
                rendering_view_id=plan.rendering_view_id, rendering_digest=plan.rendering_digest,
                policy_version=plan.policy_version,
            )

    outcomes: list[AdapterUnitOutcome] = []
    for unit in plan.units:
        # 134E.6V finding (BLOCKING, repaired): an adapter's deliver_fn
        # raising was previously left unhandled, propagating out of
        # execute_delivery() entirely and aborting the whole execution --
        # violating the explicit requirement that adapter exceptions be
        # handled deterministically and that the pipeline fail safely.
        # A raised exception is normalized into the identical
        # AdapterUnitOutcome shape a well-behaved adapter would return
        # for a transport failure: not delivered, conservatively
        # retryable (an exception carries no evidence the failure is
        # permanent), with the exception text captured as the
        # diagnostic. Remaining plan units still execute in order --
        # one unit's crash never silently aborts sibling units.
        try:
            outcomes.append(adapter.deliver_fn(unit))
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any
            # adapter implementation error must be normalized, not crash
            # the generic pipeline.
            outcomes.append(AdapterUnitOutcome(
                unit_id=unit.unit_id, delivered=False, retryable=True,
                adapter_response_ref=None,
                diagnostic=f"adapter raised {type(exc).__name__}: {exc}",
            ))

    delivered_count = sum(1 for o in outcomes if o.delivered)
    failed_count = len(outcomes) - delivered_count
    partial = 0 < delivered_count < len(outcomes)

    if not outcomes:
        overall = DeliveryOutcome.INVALID_PLAN
    elif delivered_count == len(outcomes):
        overall = DeliveryOutcome.DELIVERED
    elif delivered_count == 0:
        overall = DeliveryOutcome.FAILED
    else:
        overall = DeliveryOutcome.PARTIALLY_DELIVERED

    any_retryable = any(not o.delivered and o.retryable for o in outcomes)
    if overall == DeliveryOutcome.DELIVERED:
        retry_rec = RetryRecommendation.NOT_APPLICABLE
    elif any_retryable:
        retry_rec = RetryRecommendation.RETRY_RECOMMENDED
    else:
        retry_rec = RetryRecommendation.RETRY_NOT_RECOMMENDED

    return DeliveryExecutionResult(
        logical_delivery_id=plan.logical_delivery_id, adapter_id=plan.adapter_id,
        adapter_version=plan.adapter_version,
        destination_classification=plan.destination_classification,
        selected_mode=plan.selected_mode, requested_unit_count=len(plan.units),
        attempted_unit_count=len(outcomes), delivered_unit_count=delivered_count,
        failed_unit_count=failed_count, unit_outcomes=tuple(outcomes),
        overall_outcome=overall, partial=partial, retry_recommendation=retry_rec,
        diagnostics=(), rendering_view_id=plan.rendering_view_id,
        rendering_digest=plan.rendering_digest, policy_version=plan.policy_version,
    )


def plan_retry(plan: DeliveryPlan, previous_result: DeliveryExecutionResult) -> DeliveryPlan:
    """Build a retry plan covering only the previously-failed units.

    Preserves the exact same ``logical_delivery_id`` (retries never
    create a new logical delivery). Fail-closed if ``previous_result``
    does not belong to the same logical delivery -- this also
    structurally rejects "changed content retry", since a changed
    rendering produces a different ``logical_delivery_id`` by
    construction (``compute_logical_delivery_id`` includes the
    rendering digest).
    """
    if previous_result.logical_delivery_id != plan.logical_delivery_id:
        raise ValueError(
            "Cannot build a retry plan: previous_result belongs to a different "
            "logical delivery"
        )
    failed_unit_ids = {o.unit_id for o in previous_result.unit_outcomes if not o.delivered}
    if not failed_unit_ids:
        raise ValueError("Cannot build a retry plan: no failed units to retry")
    retry_units = tuple(u for u in plan.units if u.unit_id in failed_unit_ids)
    return DeliveryPlan(
        logical_delivery_id=plan.logical_delivery_id, adapter_id=plan.adapter_id,
        adapter_version=plan.adapter_version,
        destination_classification=plan.destination_classification,
        selected_mode=plan.selected_mode, units=retry_units,
        policy_version=plan.policy_version, content_preserved=plan.content_preserved,
        diagnostics=plan.diagnostics, rendering_view_id=plan.rendering_view_id,
        rendering_digest=plan.rendering_digest,
    )


# ═══════════════════════════════════════════════════════════════════════
# Initial isolated adapters: Recording and Null
# ═══════════════════════════════════════════════════════════════════════

RECORDING_ADAPTER_ID = "recording_v1"
NULL_ADAPTER_ID = "null_v1"

_recording_log: list[DeliveryUnit] = []


def _recording_deliver_fn(unit: DeliveryUnit) -> AdapterUnitOutcome:
    """No external I/O. Records the unit in an in-memory log (test/
    inspection only, never authoritative) and deterministically
    reports success.
    """
    _recording_log.append(unit)
    return AdapterUnitOutcome(
        unit_id=unit.unit_id, delivered=True, retryable=False,
        adapter_response_ref=f"recording:{unit.content_hash}", diagnostic=None,
    )


def get_recording_log() -> tuple[DeliveryUnit, ...]:
    return tuple(_recording_log)


def clear_recording_log() -> None:
    _recording_log.clear()


def _null_deliver_fn(unit: DeliveryUnit) -> AdapterUnitOutcome:
    """Performs no delivery. Never pretends success -- always reports
    ``delivered=False`` with an explicit diagnostic. In practice this
    function is unreachable through ``execute_delivery()`` because the
    null adapter's ``always_disabled=True`` capability short-circuits
    execution before any unit is attempted; it exists so the adapter's
    own contract remains honest even if invoked directly.
    """
    return AdapterUnitOutcome(
        unit_id=unit.unit_id, delivered=False, retryable=False,
        adapter_response_ref=None, diagnostic="disabled adapter: delivery not attempted",
    )


register_adapter(DeliveryAdapter(
    capabilities=AdapterCapabilities(
        adapter_id=RECORDING_ADAPTER_ID, adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown", "text/plain", "application/json"}),
        supported_modes=frozenset({DeliveryMode.INLINE, DeliveryMode.ATTACHMENT, DeliveryMode.MULTIPART_INLINE}),
        max_inline_bytes=8000, supports_attachment=True,
        represents_external_delivery=False, safe_destination_alias="recording:memory",
    ),
    deliver_fn=_recording_deliver_fn,
))

register_adapter(DeliveryAdapter(
    capabilities=AdapterCapabilities(
        adapter_id=NULL_ADAPTER_ID, adapter_version="1.0",
        supported_media_types=frozenset({"text/markdown", "text/plain", "application/json"}),
        supported_modes=frozenset({DeliveryMode.INLINE}),
        max_inline_bytes=8000, supports_attachment=False,
        represents_external_delivery=False, safe_destination_alias="disabled:none",
        always_disabled=True,
    ),
    deliver_fn=_null_deliver_fn,
))
