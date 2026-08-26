# Phase 149O.20L.7O.3K Complete — Post-RI Attachment Architecture and Release Decision

**Verdict: COMPLETE. DECISION-ONLY. NO SRC/PCAE MODIFIED.**

Re-derived, from current source and contracts only (not inherited from
3I/3J/3J.1's own conclusions), whether PCAE can now safely complete
true RI-backed Advisory reasoning consumption (Repository Intelligence
→ canonical `AdvisoryContextPackage` → real `AdvisoryProvider` →
Advisory result), or should instead ship 3J's already-verified
attachment-only integration as a patch, or defer RI work entirely.

**Advisory subsystem taxonomy:** freshly enumerated 7 distinct
production subsystems: `core/advisory.py` (Phase 88W, deterministic
decision engine, no reasoning step); `advisory/context/advisory_context_builder.py`
(Phase 122E, RI-context builder); `core/advisory_repository_skills.py`
(Phase 115R, `AdvisoryProvider` framework); `core/advisory_context_package.py`
(Phase 115X, `AdvisoryContextPackage`); `core/current_acting_model_advisory_provider.py`
(Phase 115S); CLI surfaces (`commands/advisory.py`,
`commands/advisory_context.py`); Advisory Runtime (Phase 113A,
architecturally distinct, unrelated to RI).

**AdvisoryProvider maturity: MOCK-ONLY / DISCONNECTED BY DESIGN.**
Independently re-confirmed via `grep -rn` over `src/pcae/*.py`
(excluding `__pycache__`): `advisory_repository_skills.py` and
`advisory_context_package.py` have zero non-test importers anywhere in
production code, exactly as each module's own docstring states.

**Phase 122 intended consumer:** directly re-read
`docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md`
§3.4: 122A itself states that placing Repository Intelligence content
into a specific `AdvisoryContextPackage` section requires "an explicit
115W-contract amendment or extension phase" that 122A does not
authorize by itself. **A new contract is required for Option A.**

**True-consumption acceptance test applied:** a different valid RI
context must be capable of producing a different Advisory reasoning
output, with authority fields remaining structurally separate.
`core/advisory.py`'s `would_*`/`broker_decision`/`advisory_decision`
fields are structurally invariant to RI (re-confirmed from source, not
re-stated from 3J.1's own A/B test); the `AdvisoryProvider` chain has
no automatic invocation path to test against at all. **Conclusion: RI
currently affects zero Advisory reasoning output anywhere in this
repository — the present state is attachment/disclosure only.**

**Effort reclassification: L, not 3I's S.** 3I's S estimate scoped
only the attachment work 3J implemented. True consumption additionally
requires: a 115W contract amendment; a real (non-mock, non-human-relay)
`AdvisoryProvider` implementation — the only non-mock provider today,
`CurrentActingModelAdvisoryProvider`, requires its answer supplied at
construction time by whichever operator is running the session, not a
live call; a new production entry point (zero existing call sites to
wire from); and F1 repair as a precondition.

**Authority separation:** already structurally guaranteed by the
existing 115Q/115R architecture (`RawAdvisoryResponse`'s
`_UNAUTHORIZED_RESPONSE_FIELDS` rejects `verdict`/`commit`/`push`/
`authorized`/`execute`/`finalize` outright; `performed_flags` always
`False`) — a genuine asset for any future Option-A phase, requiring no
redesign.

**F1 symlink provenance disposition:** ACCEPTABLE NON-BLOCKING for the
current attachment-only state (unchanged from 3J.1's own disposition,
independently re-confirmed). **MUST REPAIR BEFORE TRUE REASONING
CONSUMPTION** — a poisoned or foreign snapshot silently consumed (the
zero-commit case) could feed fabricated content into an actual
reasoning output under Option A, a materially different risk class
than today's diagnostic-only impact.

**Reasoning threat model (not implemented, assessed only):** artifact
integrity, context poisoning, and prompt injection are unaddressed by
any frozen contract today — further evidence Option A is
architecture/contract-scale work.

**Candidate comparison:** rollback readiness/evidence (Candidate A, per
3I) remains S-M effort, LOW risk, and now outranks a future Option-A
attempt given Option A's reclassified L effort. Runtime preflight
(Candidate B) remains lowest priority, not reopened.

**Recommendation: OPTION B.** Release 3J's already independently
verified (3J.1) attachment-only integration as a narrow patch
(`v0.4.2`-plausible) with corrected release language ("`pcae advisory
check` now automatically attaches available Repository Intelligence
context, provenance, and limitations" — never "RI now drives Advisory
reasoning"), and reprioritize Candidate A as the next capability ahead
of any future true-reasoning-consumption attempt.

**Project-status terminology corrected:** `PROJECT_STATUS.md`'s Current
Phase section updated to record this phase's findings and to keep the
122A-scoped Advisory-reasoning-consumption gap explicitly **open** —
this phase does not close it. No historical phase report was rewritten.

**Blocking count: 0.**

Article remains **STOPPED**; `~/repos/pcae-deepseek-research`
untouched, out of scope, not inspected. `v0.4.1` remains the current,
unmodified public release; no release action taken. No version bump,
no tag, no F1 repair, no provider/model call, no Candidate A/B
implementation, no runtime/authority/Permission Broker/HATP/HMIC/
Class-B/CLTR/Dell change occurred this phase.

**This phase does not begin its own recommended next phase.**

```
ADVISORY MODE ATTACHMENT:
VERIFIED
TRUE RI-BACKED ADVISORY REASONING:
NOT YET PRODUCTION-READY
ADVISORY PROVIDER:
MOCK-ONLY / DISCONNECTED
RECOMMENDED:
OPTION B (release attachment-only patch; reprioritize Candidate A next)
IMPLEMENTATION:
NOT STARTED

HUMAN PRIORITY / RELEASE SELECTION:
REQUIRED
```

See
`docs/PHASE_149O_20L_7O_3K_POST_RI_ATTACHMENT_ARCHITECTURE_AND_RELEASE_DECISION.md`
for full evidence, taxonomy, decision matrix, and threat-model notes.
