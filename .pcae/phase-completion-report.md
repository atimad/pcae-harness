# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.2 — Human-Principal Authentication, Protected Approval Presentation, and Proof-Lifecycle Implementation Planning

Canonical hand-authored completion content is the required phase document:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_2_HUMAN_PRINCIPAL_AUTHENTICATION_PROTECTED_APPROVAL_PRESENTATION_PROOF_LIFECYCLE_IMPLEMENTATION_PLANNING.md`.

Verdict: IMPLEMENTATION PLANNING COMPLETE. Produced a bounded, 8-layer
staged implementation plan realizing the verified contract baseline
(RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0, RDGO-001
v3.0, RPAC-001 v1.0 unchanged) frozen by 149O.20L.7O.3W.1R.2B.1R.1.1R.1.
Every new normative requirement across the six contracts is mapped
(Matrix A) to existing reusable code, a new component/schema/store/
validator/test, or an explicitly deferred real-hardware dependency; no
requirement left unmapped. B1/B7/N1/N2 production repairs are grounded in
exact file/line citations from current source (`runtime_authority.py`,
`runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`),
not re-descriptions of contract text (Matrix D). Layers are not collapsed:
canonical models/stores and deterministic protected-presentation/proof
fixtures come first; real FIDO2 and real protected UI are explicitly
deferred to Phases 3/4; B1/B7/N1/N2 repair is sequenced into Phase 2 (shape)
and Phase 5 (full N2 closure, which depends on Phases 1-4 existing).
Recommended first implementation slice: HumanPrincipalRegistry model/store +
TrustedApprovalPresentationEvidence model/store + HumanAuthenticationProof +
HPACLifecycleStore model/store + deterministic non-real
HumanAuthenticator/ProtectedApprovalPresentationMechanism implementations,
with no PB integration and no `runtime_authority.py` change in this first
slice. All five required matrices (A-E) and all 55 required sections
present. No production, test, hardware, execution, POL-005, runtime,
release, article, or private-research change; runtime remains
`Observed / observe / unavailable`; release `v0.4.3` (`63580893`) unchanged.

Exact next, not begun: the first bounded implementation phase (canonical
human-principal/presentation/proof-lifecycle models and stores plus
deterministic authenticator/presentation fixtures). Human decision required
before any implementation code is written.
