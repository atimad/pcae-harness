# BR-005 Retrospective: Execution Governance Activation

BR-005 (`execution_governance_activation` track, Phases 69A–69O) took PCAE
from a governance-and-observability framework into a system that can
actually write to, and reverse writes in, the root repository — under
explicit human authorization at every step. This document is a retrospective
on what was built, the decisions that shaped it, the risks accepted along
the way, and what is deliberately still missing.

## What BR-005 Achieved

Starting from a runtime activation architecture review (69A) and an approval
store (69B), BR-005 built one continuous, evidence-gated chain:

1. **Approval and authorization** (69B–69E) — a human approves a specific
   prompt/agent pair (APA), invocation and runtime contracts are validated
   (69C), all required gates are evaluated together into a single pathway
   (69D), and the authorized invocation is recorded (ARA, 69E).
2. **Audit and activation** (69F–69H) — an append-only audit record is
   created for the attempt (EAR, 69F), the invocation runs inside a sandbox
   and produces a result record (ERR, 69G), and the result is classified
   along technical-status, governance-attention, and severity axes (69H).
3. **Result review and change detection** (69I–69K) — a human records a
   disposition on the result (ERRA, 69I), and snapshot/change detection
   (ESA/ECR) is integrated automatically rather than requiring a manual step
   (69J–69K).
4. **Sandboxing** (69L) — the invocation moves from running against root to
   running inside an isolated `git worktree` + `rsync` overlay workspace.
5. **Change capture and promotion review** (69M) — the Execution Change
   Package (ECP) captures full diff/content/hash evidence from the sandbox
   before it is destroyed, and a human records a content-level promotion
   review (EPR) against that evidence.
6. **Governed promotion** (69N) — `pcae promote` becomes the first command in
   PCAE's history to mutate root, gated strictly on `EPR.promotion_authorized=True`.
7. **Governed rollback** (69O) — `pcae rollback` becomes the second (and so
   far only other) command to mutate root, reversing a specific promotion
   using the evidence captured in step 5.

The result: PCAE can take an AI agent's sandboxed output, capture it as
evidence, have a human review and authorize it, write it to root, and — if
needed — reverse that exact write, with every step leaving a durable record
and `execution_allowed=False` enforced throughout. See
[docs/ARCHITECTURE.md](ARCHITECTURE.md) for the full artifact model and
lifecycle descriptions.

## Major Architectural Decisions

- **Mutation is isolated to two commands.** Rather than letting any
  governance command grow the ability to write, root mutation was deliberately
  confined to `pcae promote` and `pcae rollback`, each consuming a specific
  prior-phase artifact (EPR, PER) as its sole authorization source.
- **Evidence capture is a mandatory *attempt*, not a mandatory *success*.**
  Phase 69M's Condition 14 established that post-execution evidence capture
  (ECP) must always be attempted and its failure must always be recorded
  (`capture_outcome="failed"`), but a capture failure cannot retroactively
  flip `execution_occurred` back to `False`. Pre-execution conditions block;
  post-execution conditions can only record.
- **Resumability through idempotent skip, not a `--resume` flag.** Both
  promotion and rollback detect already-applied / already-reverted paths via
  content-hash divergence checks and skip them silently (recorded, not
  errored), rather than introducing separate resume semantics. The same
  command, re-run, naturally finishes a partial run.
- **Divergence blocks the whole attempt, never partially proceeds.** If any
  single path's content has diverged from the evidence's expectation, the
  entire promotion or rollback aborts before any file is touched
  (`status="aborted_divergence"`). EPR's `override_divergence` field exists
  but is deliberately never consumed — overriding divergence was scoped out,
  not silently wired in.
- **Strategic decisions are lineage, not mutable state.** Phase 65J's
  distinction — that `.pcae/strategic-lineage.json` is an append-only record
  of *why*, separate from roadmap state and activation evidence — was load-bearing
  throughout BR-005: every phase transition (69B→69C→...→69O) added a new SLR
  that supersedes the previous one by reference, never by mutation.
- **Workspace isolation, not OS containment, for 69L.** Given the constraint
  of no new infrastructure dependency, sandboxing was implemented as a `git
  worktree` + `rsync` overlay with the subprocess `cwd` redirected — a real,
  testable isolation boundary for relative working-tree changes, explicitly
  not claimed as filesystem, process, or network containment.

## SLRs That Shaped the Implementation

Each phase from 69L onward recorded a Strategic Lineage Record (SLR)
documenting its accepted scope. The most consequential:

**SLR-69L (Execution Sandboxing, 6 entries):** sandbox provider fixed to
`git worktree` (container providers deferred); OS-level isolation deferred —
workspace isolation is development containment only; sandbox directories are
ephemeral, no forensic copy retained; ECR captures paths, not content
(closed by ECP in 69M); workspace isolation is behavioral, not OS
containment — absolute-path writes are uncontained; the sandbox shares
git's object store with root, so commits made inside it land in the same
object database.

**SLR-69M (ECP/EPR, 10 roadmap-debt entries):** scope is ECP + EPR only —
no promotion execution, no rollback, no git commit/push, no automatic
promotion in this phase; hard exclusions (`.git/`, `.pcae/`, external
symlink escapes) cannot be overridden by any review; divergence and
git-commit-in-sandbox detection are evidence, not blockers on their own.

**SLR-69N (Promotion Execution, 10 roadmap-debt entries):** promotion is
gated on EPR alone, never on ECP directly; `already_applied` paths from a
prior partial run are skipped, not re-written; any conflict aborts before
any write; rollback execution, automatic promotion, and divergence-override
consumption are explicitly out of scope for 69N.

**SLR-69O (Rollback Execution, 10 entries — the closing set for BR-005):**

1. RER is the first artifact reversing a root mutation; gated on
   `PER.status in {completed, partial}` and `PER.rollback_payload_available=True`.
2. `file_plan` is derived strictly from `PER.file_results` where
   `outcome="success"`; `already_applied` PER entries are excluded.
3. Divergence is inverted from 69N: current hash vs. `after_hash` (pending) /
   `before_hash` (already_reverted) / neither (conflict).
4. Any conflict blocks the entire attempt before any file is touched.
5. Partial rollback is a valid terminal state, not automatically retried.
6. RER is created before the first restore and persisted after every file;
   interruption is always a stored record.
7. `mark-interrupted` is bookkeeping only — it never writes files.
8. Rollback is idempotent via the `already_reverted` skip; there is no
   `--resume` command.
9. Rollback-of-rollback is forbidden by construction — no `rer_id`-accepting
   entry point exists.
10. No automatic rollback, no git commit/push, no override-divergence
    support, no multi-PER batch rollback, no user-specified paths.

## Risks Intentionally Accepted

- **The sandbox is not a security boundary against a malicious or
  arbitrary-path-writing process.** Workspace isolation contains relative
  working-tree changes; it does not stop an absolute-path write or a network
  call. This was accepted because BR-005's threat model is *ungoverned
  promotion to root*, not *arbitrary sandboxed code execution* — the latter
  remains explicitly deferred (`production_containment_ready=False`).
- **Sequential, non-atomic file writes during promotion and rollback.**
  A promotion or rollback that fails partway through leaves some files
  written and some not, recorded as a `partial` status. This was accepted in
  favor of incremental PER/RER persistence (so an interrupted run is never
  silently lost) over the larger mechanism of staged-rename atomic commits.
- **`override_divergence` is recorded but inert.** EPR carries a field for a
  human to express intent to override a divergence conflict, but no consumer
  reads it. This was a deliberate choice to ship the simpler, stricter
  behavior (divergence always blocks) rather than build and validate an
  override path inside the same phase that introduced root mutation.
- **No multi-PER batch rollback.** Each rollback targets exactly one PER.
  Accepted to keep the first rollback implementation's blast radius small
  and auditable, at the cost of requiring multiple invocations to undo a
  multi-step promotion history.

## Remaining Gaps

- **Phase Activation Governance is still unresolved.** PCAE has no
  first-class artifact that separates "implementation approved" from
  "activation approved" from "commit approved" from "push approved." This
  predates BR-005 (flagged at Phase 65J) and was not resolved by it — BR-005
  was implemented and is capability-complete, but Phase 69O remains the
  formally active phase in the roadmap registry pending a future, explicit
  activation decision for whatever comes next.
- **No git commit or push automation anywhere in the chain**, by design —
  this is a gap relative to a fully autonomous workflow, not relative to
  BR-005's stated scope.
- **Rollback-of-rollback, multi-PER batch rollback, and divergence-override
  consumption** remain unimplemented, as documented in SLR-69O-009/010.
- **Container or OS-level sandbox providers** were never built; `git
  worktree` workspace isolation is the only provider.

## Lessons Learned

- **Naming collisions across a long-running roadmap are a real hazard.**
  69N's `_PXR_*` prefix was chosen specifically to avoid colliding with a
  pre-existing Phase 45N `_PER_*` ("Prompt Execution Readiness") constant
  that was discovered mid-implementation and had been silently shadowed.
  Grepping for an acronym before reusing it is now a de facto practice.
- **Resumability is simpler as an idempotent skip than as a resume flag.**
  Both 69N and 69O independently converged on the same pattern — detect
  already-done work via content hashing and skip it — rather than building
  separate resume machinery. This emerged from real necessity (a partial
  promotion/rollback must be safely re-runnable) rather than upfront design.
  Mirrored mechanisms across promotion and rollback meant the second
  implementation (rollback) was substantially de-risked by the first
  (promotion).
- **Post-execution conditions need different rules than pre-execution
  ones.** Phase 69M's Condition 14 (the first post-execution governance
  condition) required explicitly stating that capture failure cannot
  retroactively block an execution that already happened — a distinction
  that pre-execution conditions never needed to make.
- **Documentation and roadmap registries drift quietly unless regeneration
  is treated as part of the work, not cleanup after it.** Every phase in
  BR-005 regenerated `docs/COMMANDS.md`, `docs/ROADMAP_REGISTRY.md`, and
  `docs/CAPABILITY_INVENTORY.md` as part of the same change, which is why
  this retrospective and the post-69O documentation consolidation found
  those three files already accurate — the drift that needed fixing was
  concentrated in the hand-maintained narrative docs (`README.md`,
  `docs/ARCHITECTURE.md`) that don't get regenerated automatically.
