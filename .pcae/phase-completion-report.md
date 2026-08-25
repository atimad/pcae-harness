# Phase 149O.20L.7O.3J Complete — Repository Intelligence to Advisory Production Consumption Integration

**Verdict: COMPLETE. BOUNDED SOURCE-MODIFYING INTEGRATION. ZERO BLOCKING FINDINGS.**

Per the human's Plan A / Candidate C selection from `149O.20L.7O.3I`,
wired the real production Advisory decision path
(`core/advisory.py::build_advisory()`, the engine behind `pcae
advisory check`) to automatically consume the existing,
already-built-and-tested Repository Intelligence Advisory-context
bridge (`advisory/context/advisory_context_builder.py::build_advisory_context()`),
which previously had exactly one caller — the manual `pcae advisory
context build` CLI command.

**Production diff scope:** exactly one file changed
(`src/pcae/core/advisory.py`, +112/-0 lines) — a new, additive
`repository_intelligence_context` key on the Advisory output envelope.

**Acquisition mode: READ-ONLY QUERY.** Reads
`.pcae/repository-intelligence/latest.json` at its existing canonical
pipeline-defined path (`repository_intelligence/persistence.py::
DEFAULT_OUTPUT_SUBDIR`); no snapshot regeneration, no new `.pcae/`
writes.

**Missing/invalid/stale RI state:** fail-soft (not fail-closed) for
missing or invalid/incompatible-schema snapshots — a deliberate,
documented divergence from `build_advisory_context()`'s own
fail-closed default for its CLI caller, scoped to this one call path.
Staleness is disclosed via the snapshot's own already-recorded
`repository_commit` provenance field compared against current `git
rev-parse HEAD`, appended as a limitation entry using the pre-existing
free-form limitation shape — no new freshness policy was invented.

**Authority non-flow:** `repository_intelligence_context` is computed
and inserted only after all broker/decision fields are already fully
resolved from `build_permission_broker()` alone, so it cannot
causally influence `broker_decision`/`advisory_decision`/`would_*`/
`authorization_granted`/`execution_authorized` — independently
verified by a dedicated test comparing identical evidence inputs with
and without RI context present.

**Permission Broker isolation:** zero references to
`permission_broker`/`PermissionBroker` in the RI or advisory-context
subsystems, re-confirmed unchanged by static test.
`mutation_permission.py`/`permission_broker.py` were not modified.

**No model/provider/network dependency added.** `pcae advisory
context build` (manual CLI) remains byte-unmodified and independently
re-verified working end-to-end via subprocess.

**Tests:** 18 new `fast_green` tests added
(`tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py`),
all passing — automatic consumption, entity-lookup identity binding,
missing/invalid/incompatible-schema/stale RI disclosure,
cross-repository isolation, determinism, authority non-flow, static
Permission Broker isolation, static no-self-CLI-subprocess check, CLI
regression (both commands), and runtime-boundary preservation.

**Regressions:** full pre-existing Advisory/RI regression corpus
(2848 tests, 22 files) passes except 7 failures independently
re-confirmed identical against the unmodified pre-3J tree via `git
stash` — pre-existing, unrelated.

**Fast Green:** pre-3J baseline (via `git stash`) 336 pre-existing
red / 8731 passed / 9 errors; post-3J 352 red / 8733 passed / 9
errors. Exact node-ID diff: 16 new red node IDs, all of the literal
form "no `src/pcae` file changed since a fixed historical phase-entry
commit" (pre-existing structural tripwires that necessarily fire for
any legitimate source-modifying phase), 0 resolved. Reconciliation:
8731 minus 16 plus 18 new tests equals 8733. **This phase's own
attributable derived-correctness result: 0 failed.**

**Runtime unchanged:** `Observed`/`observe`/`unavailable` before and
after this phase.

**Deferred, not touched:** Candidate A (rollback readiness/evidence
auto-generation) and Candidate B (runtime preflight capability-aware
routing), per the human's Plan A selection.

**This phase does not self-certify.**

```text
REPOSITORY INTELLIGENCE -> ADVISORY PRODUCTION CONSUMPTION: IMPLEMENTED
REAL ADVISORY PATH: AUTO-CONSUMES EXISTING RI CONTEXT BUILDER
MANUAL ADVISORY-CONTEXT CLI PREREQUISITE: REMOVED
RI AUTHORITY: NONE / UNCHANGED
PERMISSION BROKER: NOT INFLUENCED BY RI CONTEXT
ATTRIBUTABLE REGRESSIONS: 0
INDEPENDENT END-TO-END VERIFICATION: MANDATORY NEXT
```

**Recommended next phase: `149O.20L.7O.3J.1` — Independent End-to-End
Repository Intelligence / Advisory Consumption Verification.** Not
begun.

Article remains **STOPPED**, not resumed. `~/repos/pcae-deepseek-research`
untouched.

See `docs/PHASE_149O_20L_7O_3J_REPOSITORY_INTELLIGENCE_ADVISORY_PRODUCTION_CONSUMPTION_INTEGRATION.md`
for the full evidence trail.
