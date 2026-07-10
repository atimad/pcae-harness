# Phase 132A - Repository Intelligence Service Architecture

## 1. Purpose

Tracks 119-131 built, hardened, and unified a deterministic knowledge
substrate: Repository Knowledge Snapshot, Dependency Knowledge Graph,
Historical Memory, Change Impact, Advisory Context, Cross-Artifact
Integration, and - as of Track 131, independently verified complete -
a single Unified Query access layer over all six. That substrate
answers **"where is the information?"** - given a category and a
target, Unified Query locates, correlates, aggregates, exposes, and
references exactly one artifact family's (or one explicitly-declared
relationship's) worth of content, bounded, deterministic, and
governed.

**Unified Query alone is intentionally insufficient for higher-level
consumers**, for a reason inherent to its own frozen contract, not a
gap to be closed by expanding it further:

- **Unified Query is single-request, single-category by design**
  (131B Section 7's routing contract - a fixed category-to-family
  mapping, one request in, one bounded response out). A consumer that
  needs "everything currently known about entity X" - its repository
  position, its dependency neighborhood, its historical record, any
  change impact naming it, any advisory context that selected it, any
  cross-artifact relationship touching it - must today issue up to six
  separate Unified Query calls, one per family, and has no governed,
  deterministic way to combine their results.
- **Composition is explicitly out of Unified Query's scope.** 131B
  Section 6 closes Unified Query's own responsibility list to
  "locate/correlate/aggregate/expose/reference" *within a single
  routed request* - it does not authorize assembling *multiple*
  routed requests' results into one coherent, provenance-complete
  package. Extending Unified Query itself to do this would be exactly
  the kind of scope creep 131B's own closed responsibility list was
  designed to prevent (mirroring 130A/131A's own recurring lesson:
  each layer's contract stays narrow so a higher layer can compose
  without duplicating logic).
- **Every current and named future consumer** (Advisory, Repository
  Skills, CLI tooling, reporting) needs composed, multi-family answers,
  not single-category fragments. Today, each consumer that wants more
  than one family's content must either issue multiple raw queries
  itself (duplicating composition logic per consumer) or go without
  (as Advisory currently does - Section 3 below).

**This is why Repository Intelligence Service exists**: it is the
**consumption layer** - the canonical, single place where "assemble a
complete, governed, multi-family Repository Intelligence answer" is
implemented exactly once, so that Unified Query's own contract can
stay narrow and every consumer gets identical composition guarantees
instead of reinventing them.

**Repository Intelligence remains the knowledge layer. Repository
Intelligence Service becomes the consumption layer.** This phase is
architecture only: no implementation, no schema change, no source
code, no test code, no runtime behavior change.

## 2. Position within PCAE

```
Repository
    |
    v
Repository Intelligence          (Tracks 119-130: the six knowledge
    |                             artifact families + Cross-Artifact
    |                             Integration - "where is the
    |                             information?")
    v
Unified Query                    (Track 131: single deterministic
    |                             access layer - locate/correlate/
    |                             aggregate/expose/reference, one
    |                             request, one family or one declared
    |                             relationship at a time)
    v
Repository Intelligence Service  (Track 132, this phase: the
    |                             consumption layer - "how should
    |                             Repository Intelligence be consumed
    |                             consistently?" - compose/normalize/
    |                             present across multiple Unified
    |                             Query calls, preserving every
    |                             governance guarantee)
    v
Consumers                        (Advisory, Repository Skills, CLI
                                  tooling, reporting, future internal
                                  services)
```

Each layer consumes only the layer immediately below it. Repository
Intelligence Service consumes Unified Query; it does not read
artifact files directly, does not call artifact-family generators,
and does not bypass Unified Query's own routing/identity/provenance
guarantees to reach into a family's content directly - this mirrors
131A Section 4's own layering discipline (the Query Layer itself
never reads a family's raw file when a lower-level accessor already
exists) applied one level higher.

### 2.1 Where existing consumers stand today

Direct re-inspection confirms today's actual consumption pattern,
which this architecture is designed to eventually let consumers
migrate away from (a future, separately-scoped decision - not this
phase's own scope, Section 15):

- **Advisory** (`src/pcae/advisory/context/advisory_context_builder.py`)
  consumes Repository Intelligence via Track 121's `execute_query`
  directly - a single-family, RKS-only path, translated straight from
  `AdvisoryContextRequest` to `QueryRequest` with no composition
  across families.
- **Repository Skills** (`src/pcae/core/advisory_repository_skills.py`,
  Phase 115R) is a deterministic, mock-backend-only framework today,
  disconnected from Repository Intelligence entirely (confirmed by
  its own module docstring: "this module is never imported by
  `core/decision_evaluation.py`...").
- **No consumer today** composes across more than one Repository
  Intelligence family in a single governed operation. Repository
  Intelligence Service is the first architectural answer to that gap.

## 3. Responsibilities

### 3.1 Repository Intelligence Service shall

- **consume Unified Query** - every piece of Repository Intelligence
  content the Service ever returns is obtained via one or more Unified
  Query calls, never via a direct artifact read;
- **assemble complete Repository Intelligence responses** - combine
  multiple Unified Query results (potentially spanning all six
  families) into one coherent, consumer-facing package;
- **preserve provenance** - every composed element retains the full
  six-element provenance chain Unified Query already attaches (131B
  Section 9); composition never truncates or summarizes it away;
- **preserve evidence** - verbatim, exactly as Unified Query returns
  it (131B Section 10); the Service performs no transformation of
  evidence content;
- **preserve limitations** - the union of every consumed Unified Query
  call's own limitations, plus any Service-level composition
  limitation (e.g. "family X was not queried because the request did
  not request it"), never a replacement for either;
- **preserve uncertainty** - every uncertainty category Unified Query
  records (131B Section 14) is carried into the composed response
  unchanged;
- **preserve boundary disclosures** - the same real nine-field
  `boundary_disclosure.schema.json` object Unified Query already
  attaches (131B Section 16 / 131E's own resolution of the mapping
  gap 131C found), carried forward, not reconstructed;
- **provide deterministic access** - Section 10;
- **abstract internal artifact composition** - a consumer asks for
  "everything about entity X" without needing to know which of the six
  families to query, in what order, or how to merge the results; the
  Service owns that composition logic exactly once.

### 3.2 Repository Intelligence Service shall never

- **create knowledge** - no field in a composed response may state a
  claim absent from every Unified Query result it was built from;
- **become authoritative** - Section 8;
- **reason** - no interpretation of what composed content might mean;
- **infer** - no relationship, entity, or fact created by inference;
- **recommend** - no suggested action, priority, or relevance score;
- **rank** - composed elements are ordered only by the same
  identifier-lexicographic discipline every lower layer already uses
  (Section 10), never by a computed relevance judgment;
- **evaluate** - no Decision Evaluation of any kind (Section 15's own
  non-goal, restated here as a binding prohibition);
- **authorize** - no execution authorization of any kind;
- **mutate** - no write to any artifact, Unified Query result, the
  repository, or runtime state;
- **execute** - no execution capability of any kind.

This is 131B Section 5/6's authority-and-responsibility pattern
restated one layer up: Repository Intelligence Service's own
"may/never" list is exactly as narrow, for exactly the same reason -
composition must not become a backdoor for capabilities every lower
layer already correctly refuses to grant.

## 4. Consumer Model

Documented as **responsibilities only** - no implementation, no
integration code, no consumer-side changes authorized by this phase.

- **Advisory** - a future, separately-scoped integration could let
  Advisory request a composed, multi-family package instead of its
  current single-family `execute_query` path (Section 2.1), without
  Advisory gaining any new authority by doing so (matching 122's own
  established non-authority consumption pattern, restated at this
  layer per Section 8 below).
- **Repository Skills** - a future integration could let a Repository
  Skill's evidence-gathering step request a composed package as
  deterministic input, still within the existing "no real model
  backend, no execution capability" boundary 115R already established
  and this phase does not touch.
- **CLI tooling** - a future governed CLI command (matching the
  existing `pcae repository-intelligence <family>` command family's
  own pattern) could expose composed responses for human inspection,
  read-only, exactly as every existing Repository Intelligence CLI
  command already is.
- **Reporting** - a future reporting surface (e.g. a periodic
  read-only summary) could consume composed packages as its own input,
  without becoming an authority over their content.
- **Future internal services** - any future PCAE-internal capability
  that needs multi-family Repository Intelligence content becomes a
  Repository Intelligence Service consumer by definition, rather than
  building its own composition logic against Unified Query directly -
  this is the specific architectural value this layer is meant to
  provide going forward.

No consumer integration is implemented, modified, or authorized by
this phase.

## 5. Service Lifecycle (Conceptual)

Nine conceptual stages, mirroring 131D Section 3's own nine-stage
Unified Query lifecycle one layer up - no additional stages, no
implementation:

1. **Service request** - a consumer submits a conceptual request
   (Section 6) naming what it wants composed.
2. **Request validation** - the request is checked for structural
   validity (a real target, a real requested scope) before any Unified
   Query call is made - mirroring Unified Query's own normalization
   stage (131D Section 3 stage 2), one layer up.
3. **Repository Intelligence query** - the Service issues one or more
   Unified Query calls, one per family or relationship the request's
   scope names - never a direct artifact read, never a new query
   mechanism duplicating Unified Query's own routing.
4. **Result composition** - the Service combines the returned Unified
   Query responses into one coherent structure, keyed by family, per
   Section 7's response model.
5. **Provenance assembly** - every composed element's own provenance
   chain (already complete per Unified Query's own contract) is
   carried into the composed response unchanged - the Service adds no
   new provenance element of its own beyond, optionally, a
   composition-level record of which Unified Query calls were made and
   in what order (itself provenance-worthy metadata, not a new claim).
6. **Evidence assembly** - verbatim carry-forward, per Section 3.1.
7. **Limitation propagation** - the union of every consumed call's
   limitations plus any Service-level composition limitation (Section
   3.1).
8. **Boundary propagation** - the same real boundary disclosure object
   every consumed Unified Query response already carries, propagated
   unchanged (never re-derived, never remapped - directly reusing
   131E's own "import the real object, don't reconstruct it" pattern
   one layer up).
9. **Service response** - the composed, deterministic package (Section
   7) is returned to the consumer.

**No hidden stage.** No stage in this lifecycle performs a write, a
network call, or any action outside "call Unified Query, combine
results, return."

## 6. Service Request Model (Conceptual)

No schema - conceptual categories only, for a future 132B contract to
formalize:

- **entity request** - "everything currently known about entity X" -
  the primary, consumer-facing request shape: a single stable
  identifier, resolved against whichever Unified Query categories can
  locate it, composed across every family that has content naming it.
- **artifact request** - "everything from artifact family Y" -
  narrower than an entity request; scopes composition to one specific
  family (equivalent to a single Unified Query call, wrapped in the
  Service's own response envelope for consumer-side consistency).
- **scoped request** - an entity or artifact request further narrowed
  by an explicit family allow-list (e.g. "entity X, but only
  Dependency Knowledge Graph and Historical Memory content") - the
  Service must never silently expand scope beyond what a scoped
  request names.
- **composite request** - a request naming more than one target
  entity/artifact combination to be composed into a single response
  (e.g. "entity X and entity Y, both fully composed") - conceptually
  the most complex shape; a future 132B/132D must determine whether
  this is in the first prototype's scope or explicitly deferred,
  mirroring 131D's own "start with the bounded case, defer the rest"
  discipline (131D Section 2.2).

## 7. Service Response Model (Conceptual)

No schema changes - a conceptual composed package containing:

- **requested entity** - an echo of what was asked for, deterministic
  and traceable back to the request;
- **repository knowledge** - Repository Knowledge Snapshot content, if
  the request's scope includes it and content exists;
- **dependency information** - Dependency Knowledge Graph content,
  same conditions;
- **historical memory** - Historical Memory content, same conditions;
- **change impact** - Change Impact content, same conditions;
- **advisory context** - Advisory Context content, same conditions;
- **cross-artifact references** - Cross-Artifact Integration content,
  same conditions;
- **provenance** - the full, carried-forward provenance for every
  element above (Section 5 stage 5);
- **evidence** - carried-forward verbatim content, opt-in exactly as
  Unified Query's own `include_evidence` is opt-in (131D Section 5),
  restated at this layer;
- **limitations** - Section 5 stage 7;
- **uncertainty** - carried forward per family, plus an explicit
  record for any family a composite request named but which returned
  nothing;
- **boundary disclosures** - Section 5 stage 8.

Each of the six content sections is **present only when applicable** -
a request scoped to one family produces a response with five empty/
absent sections, not five fabricated "not applicable" claims
masquerading as content. This is the same "never manufacture what
wasn't asked for or found" discipline every lower layer already
applies, restated at the composition level.

## 8. Authority Model

Repository Intelligence Service remains, without exception:

- **derivative** - every element in a composed response is a
  carried-forward Unified Query result; the Service originates no
  claim of its own;
- **read-only** - Section 11;
- **non-authoritative** - the Service is not, and does not become, a
  seventh source of Repository Intelligence content; it has no
  content of its own to be authoritative *about*.

**It never supersedes Repository Intelligence artifacts.** Where
composing multiple Unified Query results surfaces an apparent
disagreement (e.g. an entity's Repository Knowledge Snapshot state
seems inconsistent with its Historical Memory record), the Service
represents this as an explicit uncertainty/limitation - exactly as
130A Section 6 and 131B Section 4 already require one layer down -
never resolves it by preferring one family's claim over another's.

This is 131B Section 5's authority contract restated at the
composition layer: authority does not accumulate as content passes
upward through layers; every layer from Repository Intelligence
Service down to the six artifact families remains exactly as
non-authoritative as the one below it.

## 9. Relationship to Unified Query

**Unified Query**: locate, correlate, aggregate, expose, reference -
131B Section 6's own closed list, unchanged, unexpanded by this phase
or by Track 132's own planned scope (Section 15).

**Repository Intelligence Service**: compose, normalize, present,
preserve governance guarantees - a distinct, higher-level
responsibility set that does not overlap with Unified Query's own:

- **compose** - combine multiple Unified Query results into one
  package (Section 5 stage 4) - Unified Query itself never combines
  results across separate calls;
- **normalize** - present composed content in one consistent,
  consumer-facing shape regardless of which families happened to
  return content - Unified Query's own response shape is already
  normalized *per call* (131B Section 8), but says nothing about
  normalizing *across* calls;
- **present** - the consumer-facing packaging (Section 7) - Unified
  Query's own response is not itself consumer-oriented, it is a raw,
  bounded access-layer result;
- **preserve governance guarantees** - Sections 3, 8, 10-13 - ensuring
  none of Unified Query's own guarantees (provenance, evidence,
  determinism, read-only, fail-closed, boundary disclosure) is lost or
  weakened by composition.

**The Service consumes Unified Query. It never replaces it.** A
future implementation must call Unified Query's own real entry point
for every family/relationship it composes - never reimplement
routing, identity resolution, or artifact loading independently. This
directly extends 131D Section 9's "reuse Track 130's identity logic,
never duplicate it" discipline one layer up: Repository Intelligence
Service reuses Unified Query's own logic, never duplicates it.

## 10. Determinism

**Equivalent repository state plus equivalent request shall always
produce equivalent responses, except approved timestamps** - the same
two-approved-timestamp convention every lower layer already uses
(composition-envelope generation time, plus each carried-forward
Unified Query result's own timestamp fields, untouched).

- **No randomness** anywhere in composition logic.
- **No AI inference** - restated unchanged from every prior Repository
  Intelligence/Unified Query contract (125B through 131B all bind this
  identically; this phase extends the same binding one layer up).
- **Deterministic composition order** - where a composed response
  combines multiple families' content, section ordering follows a
  fixed, declared family order (matching `routing.SIX_ARTIFACT_
  FAMILIES`'s own existing fixed tuple order, Track 131's real
  precedent), and within-family element ordering follows whatever
  identifier-lexicographic discipline that family's own Unified Query
  category already applies - the Service introduces no new ordering
  rule, it only fixes the *composition* order across families.

## 11. Read-Only Architecture

Repository Intelligence Service never mutates:

- the repository;
- any of the six Repository Intelligence artifact families;
- Unified Query results;
- Evidence;
- Repository State;
- runtime state.

Every item is either a source this layer only ever reads (via Unified
Query, never directly) or a subsystem entirely outside its scope
(Evidence, Repository State, runtime state) - restating, one layer up,
the same comprehensive read-only guarantee 131B Section 14 already
holds and 131F independently re-verified via checksum comparison for
Unified Query itself.

## 12. Failure Behavior (Conceptual)

Fail closed, at minimum, for:

- **unresolved entity** - a requested entity/artifact identifier that
  no consulted Unified Query call could locate - an explicit
  uncertainty record, not a silently-empty composed response (directly
  incorporating 131F's own hard-won lesson: 131F's one BLOCKING
  finding was exactly this failure mode - a silent, empty "success" -
  occurring one layer down; this architecture explicitly requires the
  composition layer to not repeat it);
- **unsupported request** - a request naming a scope/shape this
  architecture does not define (Section 6) - fails closed, never
  silently ignored or partially honored without disclosure;
- **unavailable artifact** - a family's Unified Query call itself
  fails closed (`SnapshotLoadError`-class condition, 131B Section 15) -
  propagated as an explicit limitation on the composed response, not
  swallowed;
- **incompatible artifact** - same propagation pattern, for a
  `SnapshotCompatibilityError`-class condition;
- **ambiguous request** - a request whose scope could plausibly
  resolve against more than one interpretation with no declared
  disambiguation rule - fails closed exactly as 131B Section 7's own
  routing-ambiguity discipline requires one layer down, restated here:
  no heuristic disambiguation, ever.

**No inferred recovery.** A failure at the composition layer is never
silently worked around, retried with a different scope, or
substituted with a best-guess partial result presented as if complete.

## 13. Governance

Preserved, unchanged, extended one layer up:

- **observe-only runtime** - `pcae runtime inspect` at this phase's
  own finalization re-confirms `Observed`/`observe`/execution-
  unavailable, zero runtime plugins - Repository Intelligence Service
  introduces no runtime capability of any kind.
- **execution unavailable** - restated unchanged from every prior
  Repository Intelligence/Unified Query contract; 125G remains
  authoritative on the Execution Planning boundary, unamended by this
  phase.
- **auditability** - every composed element traces back through its
  own Unified Query provenance chain to a specific artifact and
  record, exactly as Section 8's "no independent claims" makes
  structurally true, not merely asserted.
- **explainability** - a composed response's full construction is
  explainable purely from the fixed composition order (Section 10)
  plus each element's own already-explainable Unified Query
  provenance - no hidden decision logic.
- **reproducibility** - Section 10's determinism guarantee restated as
  a testable property for a future 132C/132F to verify directly, per
  131C/131F's own precedent of independently re-deriving this rather
  than trusting prose.
- **provenance** / **evidence** - Sections 3.1/5/7-9 make both
  structurally mandatory, not optional.
- **PFN-001 compatibility** - Section 17 confirms this phase's own
  finalization satisfies it identically to every phase since 128B.2.

## 14. Extensibility

Future consumers integrate with Repository Intelligence Service
**without changing Repository Intelligence itself** - the same
"additive, never modify a lower layer" discipline Track 131 already
demonstrated in practice (131E introduced zero modifications to any
Track 119-130 file). Concretely:

- A future consumer integration adds a new caller of Repository
  Intelligence Service's own entry point(s) - it does not add a new
  Unified Query category, a new artifact-family loader, or a new
  identity-resolution mechanism, all of which remain Unified Query's
  and the six families' own exclusive responsibility.
- **Richer Advisory** - a future Advisory evolution could consume
  composed packages instead of its own current single-family path
  (Section 2.1), gaining no new authority by doing so (Section 8),
  matching Advisory's own already-established non-authority
  consumption precedent.
- **Repository Skills** - Section 4.
- **Decision Evaluation support** - a future, separately-scoped
  Decision Evaluation chapter could consume composed packages as a
  read-only knowledge input, gaining no Decision Evaluation authority
  from Repository Intelligence Service's own existence (matching
  131A Section 22's own "future relationship, no authority granted"
  pattern, restated one layer up).
- **Diagnostics / reporting** - Section 4.
- **Future internal capabilities** - any future PCAE-internal
  capability needing composed, multi-family Repository Intelligence
  content becomes a Service consumer, not a reason to expand Unified
  Query's own narrow contract (Section 9).

This section is architectural only - no consumer integration is
implemented or scheduled by this phase.

## 15. Strict Non-Goals

This phase does not design, and no future Track 132 phase may
introduce without a new, separately-scoped governed decision:

- networking;
- REST;
- GraphQL;
- HTTP;
- dashboards;
- execution;
- shell mediation;
- Decision Evaluation changes;
- Permission Broker changes;
- runtime plugins;
- execution capability.

Repository Intelligence Service is an **internal architectural
service** - a Python-level composition layer within the same process
and governance boundary every existing Repository Intelligence module
already operates inside, not a network-addressable or externally-
exposed service of any kind.

## 16. Track 132 Roadmap

Mirroring every prior Repository Intelligence/Unified Query track's
own governed lifecycle (119-131):

- **132A - Repository Intelligence Service Architecture** (this
  phase): formal chapter definition and canonical architecture.
- **132B - Repository Intelligence Service Contract Freeze**: freeze
  the binding contract this architecture establishes, resolving
  Section 6's composite-request-scope open question and any other item
  this architecture leaves conceptual rather than binding.
- **132C - Repository Intelligence Service Contract Verification**:
  independently re-derive every 132B claim from 131B's own frozen
  Unified Query contract and real source directly, mirroring 131C's
  own independent-re-derivation discipline.
- **132D - Repository Intelligence Service Prototype Plan**: define
  the bounded implementation plan - which request/response shapes
  (Section 6/7) are implemented in the first prototype versus
  deferred, mirroring 131D's own "start bounded" discipline.
- **132E - Repository Intelligence Service Prototype**: implement only
  the bounded composition layer 132A-132D authorize, reusing Unified
  Query's own real entry points directly (Section 9), never
  duplicating routing/identity/artifact-loading logic.
- **132F - Repository Intelligence Service Independent Verification**:
  independently verify 132E's implementation against this architecture
  and the 132B-132D chain, including fresh probes against edge cases
  no prototype's own test suite may have covered - directly
  incorporating 131F's own demonstrated value (Section 12).

**Recommended next phase: 132B - Repository Intelligence Service
Contract Freeze.** No phase beyond 132A is begun by this phase.

## 17. PFN-001 Confirmation

The Phase Finalization Notification Invariant (128B.2), re-confirmed
still globally binding, unamended by this phase:

- **Every terminal phase outcome** shall produce exactly one trusted
  canonical phase report delivered to the configured notification
  sink. This phase (132A) satisfies this identically to every phase
  since 128B.2.
- **Notification delivery or an explicit durable delivery-failure
  record** remains mandatory; silent omission remains prohibited.
- **No amendment.** This phase does not modify PFN-001's own contract
  text.

**PFN-001 remains globally applicable and is satisfied by this
phase.**

## 18. Confirmations

- **No implementation occurred.** This phase produced only
  documentation.
- **No runtime behavior changed.**
- **Execution remains unavailable.**

## 19. Conclusion

Track 132 - Repository Intelligence Service - is formally established
as PCAE's next architectural chapter: not an expansion of Repository
Intelligence's own knowledge substrate, but the canonical consumption
layer that composes Unified Query's own single-request, single-family
results into complete, governed, multi-family answers for every
current and future consumer. This architecture defines why Unified
Query alone is intentionally insufficient for higher-level consumers
(its own closed, narrow contract correctly excludes composition), the
five-layer PCAE position this new layer occupies, its responsibilities
and prohibitions (extending every lower layer's own non-authority/
read-only/determinism/fail-closed boundaries upward, not inventing new
ones), a consumer model naming Advisory/Repository Skills/CLI tooling/
reporting/future services without implementing any integration, a
nine-stage conceptual lifecycle mirroring Unified Query's own, a
conceptual (not schema) request/response model, an authority model
that keeps the Service exactly as non-authoritative as every layer
below it, a relationship to Unified Query that requires reuse never
duplication, determinism and fail-closed failure guarantees that
directly incorporate 131F's own hard-won silent-omission lesson, and
an extensibility strategy that lets future consumers integrate without
ever modifying Repository Intelligence itself.

This phase does not itself implement anything, does not modify any
schema, source code, or test code, and does not take any step toward
networking, REST, execution capability, or Decision Evaluation - all
of which remain correctly excluded.

No implementation occurred. No schema changed. No runtime behavior
changed. Runtime remains `Observed`/`observe`/execution-unavailable.

Recommended next phase: 132B - Repository Intelligence Service
Contract Freeze.
