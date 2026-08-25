# v0.3.2 Capability Reference — Runtime Introspection, Interactive Governance, Repository Intelligence, Authority Inspect

This is a hand-maintained reference for four capabilities independently
verified and exposed as documented product surface by Phase
149O.20L.7O.3B. `docs/COMMANDS.md` is a **generated** artifact
(`pcae docs commands`); at the time of this phase its generator did not
yet enumerate `pcae runtime inspect`, `pcae repository-intelligence`, or
`pcae authority inspect` as a top-level command area, so hand-editing it
would have created permanent drift against every future regeneration
(flagged by `pcae check` as `Generated governance artifact drift`). That
generator gap is carried forward as disclosed operational debt (not
production source; not fixed in this documentation-only phase) — see
`docs/PHASE_149O_20L_7O_3B_SELECTED_EXISTING_CAPABILITY_VERIFICATION_AND_PRODUCT_EXPOSURE.md`
§"Documentation Truth Audit" for the finding. This file is the
`docs/COMMANDS.md`-equivalent the phase brief calls for; `decision-session`
and `governance-record` are already correctly documented in
`docs/COMMANDS.md` itself (that generator does cover them) and are not
duplicated here beyond a cross-reference.

All four capabilities below were independently exercised during Phase 3B
from a clean, freshly built wheel (`pcae_harness-0.3.1-py3-none-any.whl`)
and sdist (`pcae_harness-0.3.1.tar.gz`) installed into disposable virtual
environments, against disposable git repositories outside this
repository — not against editable/development-checkout source, and (with
one documented exception) not against `pcae-harness` itself. No version
was changed; both artifacts build as `0.3.1`, matching current `HEAD`.

---

## `pcae runtime inspect`

**Side-effect class: READ-ONLY. NO EXECUTION.**

```
pcae runtime inspect
pcae runtime inspect --json
```

- **Purpose:** report PCAE's current runtime/plugin-introspection state —
  runtime lifecycle stage, execution capability, registered-plugin count,
  and the 10 declared plugin capabilities (`observe`/`advise`/`approve`/
  `deny`/`enforce`/`execute`/`audit`/`notify`/`store`/`rollback_prepare`).
- **Prerequisites:** none. Verified from a bare `git init` disposable
  repository with no `.pcae` state at all.
- **Side effects:** none observed (`git status` in the target repository
  remained clean before and after every invocation during verification).
- **Network / model invocation:** none.
- **Authority effect:** none — purely descriptive.
- **Output today (invariant, not phase-specific):**
  `Runtime state: Observed`, `Execution capability: unavailable`,
  `Maximum plugin capability: observe`, `Registry status: empty`,
  `Plugin count: 0`. This is correct and expected — no plugin loader
  exists in PCAE yet (`src/pcae/core/runtime_registry.py` owns plugin
  *metadata* only; it never loads, imports, instantiates, or executes a
  plugin). Documenting this command does not imply a plugin ecosystem
  exists; it reports the honest absence of one.
- **Non-goal:** this does not enumerate or discover third-party plugins —
  there is no plugin loader to discover them with.
- **Do not confuse with:** `pcae runtime snapshot` (bare, no
  subcommand) — a related but distinct command that previews a portable
  PCAE *governance-runtime* snapshot (active task, agent lock, session
  continuity, provenance count) and requires the target repository to
  already carry PCAE governance state; verified separately, returned
  `Snapshot readiness: not ready` against a bare disposable repository,
  as expected.
- **Tests:** `tests/test_runtime_registry_contract.py`,
  `tests/test_runtime_registry_prototype.py`,
  `tests/test_runtime_registry_verification.py`,
  `tests/test_runtime_introspection_prototype.py`,
  `tests/test_runtime_introspection_architecture.py` — 693 tests
  combined with the authority-inspect suites below, all passing at
  phase entry.

---

## Interactive governed decision workflow (`decision-session` + `governance-record`)

**Side-effect class: LOCAL GOVERNED MUTATION** (writes session/readiness/
CHGR artifacts under `.pcae/` in the *target* repository only — never a
git commit, push, or repository-content change).

Full syntax already lives in `docs/COMMANDS.md` under `## decision-session`
and `## governance-record` — that generator-produced content was
independently re-verified end-to-end in this phase and found accurate; no
changes were needed there. Summary of the verified sequence and its exact
authority semantics:

```
pcae decision-session create --template-ref <id> --subject-ref <id> --owner-id <id>
pcae decision-session evidence <session-id> --declare <evidence-id> --as-identity <id>
pcae decision-session select <session-id> --option-id <id> --options-presented <id> --template-version <v> --as-identity <id>
pcae decision-session preview <session-id> --as-identity <id>
pcae decision-session confirm <session-id> --preview-digest <digest-from-preview> --statement <text> --as-identity <id>
pcae decision-session readiness <session-id> --as-identity <id>
pcae governance-record publish <package-id-from-readiness> --operator-id <id>
pcae governance-record inspect <path-to-published-chgr.json>
pcae governance-record verify <path-to-published-chgr.json>
```

- **`create` → `Created`:** no prerequisites beyond a git repository.
- **`evidence` → `EvidenceReady`:** declares evidence references
  descriptively; does not resolve or verify referenced content.
- **`select` → `DecisionSelected`:** records the human's option choice.
  **Preview ≠ confirmation.**
- **`preview`:** renders the exact, unconditional content that
  `confirm` will bind to, and returns a `preview_digest`. Preview is a
  read of current session state; it changes nothing.
- **`confirm` → `Confirmed`:** requires the caller to echo back the exact
  `preview_digest` — this is the binding mechanism that prevents
  confirming content the human did not actually see.
  **Confirmation ≠ authorization; confirmation ≠ publication.**
- **`readiness` → `pending` package:** on first call against a `Confirmed`
  session, constructs and persists a pending-readiness package (this is a
  write). **Readiness ≠ publication.**
- **`governance-record publish` → CHGR created:** the human-authorizing
  act (IWPC-001 v1.1 §6). This is the step that actually writes a
  Canonical Human Governance Record to `.pcae/publication-execution/
  records/` in the target repository. **Publication ≠ execution** — a
  CHGR is a governance record, not permission to execute arbitrary
  actions; it authorizes nothing outside the governance-record system
  itself.
- **`governance-record inspect` / `verify`:** read-only, non-mutating
  checks against an already-published CHGR artifact.
- **CHGR** = **Canonical Human Governance Record** — a schema-conformant,
  fail-closed-validated artifact representing one completed human
  governance decision (CHGR-001). Its own inspect/verify output states
  explicitly: *"Successful schema validation means only that an artifact
  conforms to the CHGR representation contract. It does not establish
  that the represented governance act was valid, applicable, current, or
  performed by an authorized human."*

**Field-format note (observed during verification, not a defect):**
`--template-ref`, template ids embedded in confirmed sessions, and
related identifiers are validated against a closed pattern
(`^[a-z][a-z0-9_-]{2,63}$`) at CHGR construction time in
`governance-record publish`. A `template-ref` containing characters
outside that set (e.g. a colon) causes `governance-record publish` to
fail. The CLI currently reports this specific, legitimate validation
failure as a generic `internal_error` / "An unexpected internal error
occurred" rather than a more specific `invalid_request`-style message
(`run_with_error_mapping` in `decision_session.py` maps every non-
`ApplicationServiceError`/`ValueError` exception, including
`ChgrSchemaConformanceError`, to the same opaque `internal_error`). This
is a real, minor UX rough edge — not a defect that blocks documenting the
workflow, since the workflow completes correctly end-to-end with
conformant identifiers (verified live: `template-ref "manual-review"`
succeeded through to a real, inspectable, verifiable CHGR). Use
identifiers matching `^[a-z][a-z0-9_-]{2,63}$` throughout.

- **Tests:** `tests/test_phase_145g_decision_session_cli.py`,
  `tests/test_phase_145g1_decision_session_cli_repair.py`,
  `tests/test_phase_145g3_decision_session_identity_binding.py`,
  `tests/test_iwc_143o_session_coordination_publication_handoff.py`,
  `tests/test_phase_144c_publication_coordinator.py` — 197 tests, all
  passing.

---

## `pcae repository-intelligence` (self-inspection of PCAE's own repository)

**Side-effect class: `snapshot generate` is a LOCAL WRITE (writes an
artifact under `.pcae/repository-intelligence/` in the target
repository); `query`/`change-impact`/`advisory context build` are
READ-ONLY over an already-generated snapshot file.**

```
pcae repository-intelligence snapshot generate [--output <dir>] [--pretty] [--json]
pcae repository-intelligence query --snapshot <path> (--entity <id> | --capability <id> | --contract <id> | --attribution <target> | --limitations | --boundary) [--json]
pcae repository-intelligence change-impact --snapshot <path> --change <text> --entity <id> [--output <path>] [--json]
pcae advisory context build --snapshot <path> (--entity <id> | --capability <id> | --contract <id>) [--purpose <text>] [--output <path>] [--json]
```

**Critical scope finding (independently verified, differs from a naive
reading of the capability name):** `snapshot generate` requires the
current working tree to contain `src/pcae/`, `tests/`, and
`schemas/repository_intelligence/` at its top level — these paths are
hardcoded in `src/pcae/repository_intelligence/snapshot_builder.py`
(`list_top_level_entries(repo_root, "src/pcae")` and the fixed tuple
`(("tests", "test"), ("schemas/repository_intelligence", "schema"))`).
There is no `--repo-root`-style option and no configuration to point it
at a different directory layout. Verified live: running
`pcae repository-intelligence snapshot generate` from a bare disposable
repository (`git init`, one file, one commit) fails closed with:
`Error: No architectural entities could be observed at the expected
top-level locations (src/pcae, tests, schemas/repository_intelligence);
refusing to produce a non-conformant snapshot with an empty required
architectural_entities array.` The same command run from inside a real
`pcae-harness` checkout succeeds and produces a real, schema-conformant
snapshot (20 architectural entities, 2 subsystems, 5 knowledge claims, 27
knowledge sources, 4 declared unknowns against current `HEAD`).

**Conclusion:** this is **not** a general-purpose "analyze any
repository" product feature — it is a deterministic, attributed,
read-only *self-inspection* tool that only functions against a checkout
shaped like `pcae-harness` itself. It is genuinely real, deterministic,
extensively tested, and safe (every record carries explicit
attribution/verification-state/limitation/boundary-disclosure fields;
`query`/`change-impact`/`advisory context build` never write), so it is
documented here rather than removed — but it must not be marketed to
ordinary end users as "inspect your own project," since that would fail
for essentially every user's repository. It is primarily of interest to
PCAE contributors/maintainers wanting a machine-readable inventory of
PCAE's own top-level architecture.

`dependency-graph`, `historical-memory`, `cross-artifact-integration`,
`unified-query`, and `service` also exist under
`pcae repository-intelligence` but self-label "prototype" in their own
CLI help text and have zero consumers outside the CLI/tests
(`grep -rl "repository_intelligence\."` outside `repository_intelligence/`,
`advisory/`, and `commands/` returns only `cli.py`). Not documented as
supported workflows here — carried forward from 3A's classification,
unchanged.

- **Example (against a `pcae-harness` checkout):**
  ```
  $ pcae repository-intelligence snapshot generate --output /tmp/ri-out
  Repository Knowledge Snapshot generated
    Architectural entities: 20
    Subsystems:         2
    Knowledge claims:   5
    ...
  $ pcae repository-intelligence query --snapshot /tmp/ri-out/latest.json --entity "entity:src/pcae/advisory" --json
  # → attributed JSON record: entity type "module", verification_state
  #   "verified" (path-existence only), explicit limitations disclosing
  #   this observes top-level path existence only — no content/import
  #   parsing.
  ```
  Output is **descriptive** (what top-level paths exist) with explicit
  **advisory**-only boundary disclosures (`no_execution`,
  `no_repository_mutation`, `advisory_non_authority`); it is not
  evidence and not a decision.
- **Tests:** `tests/test_phase_120e_repository_knowledge_snapshot.py`,
  `tests/test_phase_121e_repository_intelligence_query.py`,
  `tests/test_phase_122e_repository_intelligence_advisory_context.py`,
  `tests/test_phase_123e_repository_intelligence_change_impact.py`,
  `tests/test_phase_124e_repository_intelligence_hardening.py` — 72
  tests, all passing. All existing tests generate against `pcae-harness`'s
  own tree (via `tmp_path`-redirected *output*, not a redirected
  *source* tree) — consistent with, not contradicting, the
  self-inspection-only finding above; no existing test exercises
  snapshot generation against an arbitrary generic repository layout.

---

## `pcae authority inspect`

**Side-effect class: READ-ONLY. NO EXECUTION. NON-AUTHORITATIVE.**

```
pcae authority inspect <path>
pcae authority inspect <path> --json
```

- **Purpose:** inspect one explicit Typed Authority Model record
  artifact file (TAMPC-001 v1.0) — CLTR authority-cutover record
  families such as `authority_epoch`, `cutover_request`, and
  `certification`.
- **Prerequisites:** an explicit file path to a record artifact of a
  supported family. There is no "inspect current authority state"
  no-argument mode.
- **It must not, and verified does not:** create, activate, transfer, or
  mutate authority; change epochs or pointers; perform cutover or
  recovery. Verified live against a real, tracked-in-this-repository
  JSON file (`.pcae/authority-evaluation/records/pointers/*.json`, an
  unrelated Authority Evaluation pointer record, not a CLTR record) —
  the command correctly refused to interpret it, returning
  `outcome: unknown_record_family` and leaving the repository (`git
  status`) unchanged.
- **Production-authority truth boundary:** `pcae cltr migration status`
  currently reports `"authority_cutover": false, "production_authority":
  "legacy"`, and no file anywhere in this repository's tracked `.pcae/`
  state (`grep -rl '"record_type"'`) declares any of the record families
  `pcae authority inspect` supports (`grep`-confirmed: the only
  `record_type` values present are `governance_record_integrity`,
  `governance_record_provenance`, `human_confirmation_evidence`, and
  `human_governance_record` — CHGR-family, not CLTR-authority-family).
  **There is currently no real, production-generated example artifact
  for this command to inspect in this repository.** It is forward-
  looking CLTR-migration-verification tooling, not a general "show me
  PCAE's current authority" command, and inspecting an artifact never
  means PCAE *possesses*, has *activated*, or has *transferred*
  authority — current production authority remains `legacy`.
- **Recommendation:** documented here as an advanced, narrowly-scoped
  CLTR-tooling command, deliberately **not** promoted to a README
  headline feature, consistent with 3A's own low-medium release-value
  rating for this candidate.
- **Tests:** `tests/test_authority_inspect_137k.py`,
  `tests/test_typed_authority_inspector_137e.py` — combined with the
  runtime-introspection suites above, 693 tests, all passing.
