# Phase 150O — Slice 1 contract-readiness stop

Exact title: PCAE-LIFECYCLE-GENERATION-PROVENANCE-PURE-MODELS-VALIDATION-SLICE-1.
Disposition: COMPLETE — NOT VERIFIED / BLOCKED.
Production symbol: NONE. Pure models were NOT implemented.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED

## Preflight

Fresh fetch: clean main, HEAD=origin/main=d5a717fd9afa936f4643a06649984a9631f23a1b,
zero outgoing, expected idle post-150N task, no agent lock. CPIPC canonical
150N parsed, alphabetic successor derived and parsed as 150O; compare=less.
No matching phase Git subject or promoted generation existed before activation.
Governed task transition/update and codex-local phase start opened exactly 150O.
No successor activated.

150N controls plus three corrected L/M nodes: 20 passed in 9.93s. The suite
runs ORIGINAL assertions against isolated historical Git fixtures; future
module/schema strings pass, historical mutations reject. This is a read-only
canonical-checkout probe; synthetic fixture commits are not canonical history.
The earlier stale prospective gate is resolved. No actual new module exists
because the separate contract blocker below stopped implementation first.

GCP-001 v1.0 SHA-256:
d72d93451a28befd39febd51473e05f020649afe26886742838a1adae119c51f.
Contract, original L/M/N artifacts and all production consumers remain unchanged.
150L's originally promoted success and later truthful blocked correction remain
historical; 150M revalidated the unchanged target and 150N fixed test boundaries.
Neither is authority to silently amend certificate byte identity.

## Blocking fact: GCP-REQ-005 digest framing

The contract requires certificate IDs to hash a domain-separated canonical body
excluding the own ID and detached proof. It does NOT define the exact domain
tag/framing bytes or an interoperable digest test vector. Both architecture
§6 and M revalidation repeat the semantic requirement without resolving that
byte-level choice. The schema literal is an interpretation domain; the text
does not expressly adjudicate schema-in-body versus separately framed hashing.

Fresh executable probes hold the same ASCII/JCS-compatible diagnostic body
constant while using (A) schema-tag + NUL + canonical-body, or (B) four-byte
length + schema-tag + canonical-body. Both domain-separate, use SHA-256 and
exclude self-ID/proof; their IDs differ. These are INCOMPLETE diagnostic data,
NOT certificates, issuance records, proposed normative encodings or root facts.
No candidate framing is selected.

This is a wire-interoperability blocker, not a claim that R6 is incoherent or
that the frozen architecture's security walls contradict each other. An exact
certificate-ID helper/parser cannot honestly be called frozen-contract exact
without selecting new byte semantics. Skipping ID validation or exposing two
algorithms would not meet this phase's acceptance criteria. Partial production
models would leave the requested model surface unverified, so none are landed.
No contract amendment or later implementation slice is begun here.

Existing HPAC canonical_json_bytes normalizes Unicode NFC and uses Python
sort_keys JSON. It is not automatically GCP's RFC-8785 canonicalization and is
not adopted, nor is HPAC imported. RootEvent has THIRTEEN wire kinds; the
ELEVEN architecture domains E1–E11 are explicitly distinct in Phase150M.
That count is NOT a new blocker and no wire kind is removed to satisfy a summary.

Smallest successor: governed GCP certificate byte-identity clarification/freeze,
including exact domain bytes/framing, own-ID exclusion, schema-specific vectors,
canonical JSON/Unicode/integer boundary vectors and verification sequencing.
Existing semantic rules stay intact; any normative change requires explicit
contract repair and independent verification. Fresh Slice1 preflight follows
that repair, not root deployment, issuance or recognition-core IV.

## Exact field inventory

All fields remain target-only; parser/model enforcement and digest tests deferred.

| # | Field | Frozen type | Frozen class | Implementation |
|---|---|---|---|---|
| 1 | schema | literal gcp-generation/1.0 | identity | NONE — blocked |
| 2 | root_epoch | opaque root-assigned string | provenance | NONE — blocked |
| 3 | repository_id | pinned provider repository identity | provenance | NONE — blocked |
| 4 | phase_instance_id | root-assigned opaque string | identity | NONE — blocked |
| 5 | phase_id | CPIPC canonical string | identity | NONE — blocked |
| 6 | task_id | canonical granted task ID | provenance | NONE — blocked |
| 7 | sequence | nonnegative integer | ordering | NONE — blocked |
| 8 | generation_id | canonical tuple [root_epoch,phase_instance_id,sequence] | identity | NONE — blocked |
| 9 | role | pending or terminal_candidate | provenance | NONE — blocked |
| 10 | report_json_sha256 | full digest | identity | NONE — blocked |
| 11 | report_markdown_sha256 | full digest | identity | NONE — blocked |
| 12 | predecessor_certificate_id | digest or null | ordering | NONE — blocked |
| 13 | input_commit | {object_format,oid,tree_oid} | provenance | NONE — blocked |
| 14 | completion_metadata_sha256 | digest | identity | NONE — blocked |
| 15 | authorization_event_id | root event ID | provenance | NONE — blocked |
| 16 | issuance_event_id | root-assigned event ID | provenance | NONE — blocked |
| 17 | certificate_id | domain-separated digest | identity | NONE — blocked |

## Requirement traceability

Machine-checkable inventory below: production_symbols=[] for every row. Static
inventory tests do not substitute for pure model behavior or root-backed proof.
Requirements not realizable in Slice1 are explicitly future-slice obligations.

| Requirement | Slice1 applicability / disposition | Production symbol | Test evidence |
|---|---|---|---|
| GCP-REQ-001 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[1] |
| GCP-REQ-002 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[2] |
| GCP-REQ-003 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[3] |
| GCP-REQ-004 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[4] |
| GCP-REQ-005 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[5] |
| GCP-REQ-006 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[6] |
| GCP-REQ-007 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[7] |
| GCP-REQ-008 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[8] |
| GCP-REQ-009 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[9] |
| GCP-REQ-010 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[10] |
| GCP-REQ-011 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[11] |
| GCP-REQ-012 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[12] |
| GCP-REQ-013 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[13] |
| GCP-REQ-014 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[14] |
| GCP-REQ-015 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[15] |
| GCP-REQ-016 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[16] |
| GCP-REQ-017 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[17] |
| GCP-REQ-018 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[18] |
| GCP-REQ-019 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[19] |
| GCP-REQ-020 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[20] |
| GCP-REQ-021 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[21] |
| GCP-REQ-022 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[22] |
| GCP-REQ-023 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[23] |
| GCP-REQ-024 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[24] |
| GCP-REQ-025 | Pure representation potentially applicable; blocked before implementation | NONE | test_all_requirements_have_honest_blocked_traceability[25] |
| GCP-REQ-026 | Root/writer/consumer/policy obligation deferred | NONE | test_all_requirements_have_honest_blocked_traceability[26] |

## Invariant traceability

- GCP-INV-001: Content digest proves byte identity, not governed issuance. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[1].
- GCP-INV-002: Every post-cutover trusted generation requires a validated issuance Target preserved, not implemented; test_invariants_are_not_claimed_implemented[2].
- GCP-INV-003: Every non-root generation has exactly one validated predecessor. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[3].
- GCP-INV-004: Historical validity requires certified membership or explicit legacy class. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[4].
- GCP-INV-005: Terminal status requires independent terminal certification. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[5].
- GCP-INV-006: Checkpoint linkage cannot establish issuance by itself. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[6].
- GCP-INV-007: Receipt linkage cannot establish issuance by itself. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[7].
- GCP-INV-008: Notification marker never establishes terminal authority. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[8].
- GCP-INV-009: Latest/current pointer never establishes provenance. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[9].
- GCP-INV-010: Incomplete provenance cannot produce complete-trust status. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[10].
- GCP-INV-011: Ambiguous chain or terminal state fails closed. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[11].
- GCP-INV-012: Legacy compatibility never fabricates missing provenance. Target preserved, not implemented; test_invariants_are_not_claimed_implemented[12].

## Events, recovery, trust and legacy inventory

| E1 issuance | isolated issuer; reviewed report/input manifest | GenerationCertificate; prior issuance or null at zero | pre-existing candidate/tree objects; issued role | exact independent approval + atomic root append; create-only |
| E2 promotion | CLI adapter; accepted issuance and exact bytes | promotion observation linked to issuance | cache write after root birth | root-bound observed manifest; no authority from placement |
| E3 pending/pre-push | issuer; accepted pending-role request | pending issuance G0/Gn | candidate commit exists, canonical code push absent | same E1 proof, NOT pre-any-commit |
| E4 governed commit linkage | primary/operator; candidate payload/input tree | immutable Git input object references | containing hash outside its own content | independent review of exact commit/tree, not author text |
| E5 push linkage | root issuer/provider observation | accept_push event | input candidate accepted at pinned canonical code ref | authenticated provider observation and ancestry checks |
| E6 checkpoint creation | local finalizer; T and immutable recovery snapshot | checkpoint + accepted binding to T | output after T; prepared cp before T is nonterminal | exact root-bound manifest, progress separate |
| E7 terminal certification | issuer; chain tail, completed task, E5, full trust | TerminalCertificate T(Gn) | source/push candidate prior to T storage commit | independent exact approval; unique phase terminal; create-only |
| E8 completion receipt | finalizer; T and actual completion/delivery evidence | receipt and root binding | output after T, immutable evidence | exact T/Gn/purpose/subject, no issuance proof |
| E9 notification publication | governed notifier; T, exact payload, intent ID | API observations/failure + root evidence binding | after T; external governance delivery only | actual provider evidence, marker derived/idempotent |
| E10 later regeneration | issuer; explicit pre-terminal successor intent | new issued generation; prior tail | before T only, including pushed-status sync | independent approval and CAS; post-T generation forbidden v1 |
| E11 historical retention | storage/reader; validated chain or legacy class | retained original bytes and proof references | no rewritten history | membership/class proof; never mtime/filename preference |

Exact RootEvent kinds: bootstrap, open_phase, authorize_manifest, issue_generation,
observe_promotion, accept_push, complete_task, certify_terminal, bind_checkpoint,
bind_receipt, record_notification, close_delivery, activate_cutover.

| CR1 report written, certificate absent | proposal only | quarantine/staging; approve exact original manifest independently or abandon; never infer issuance |
| CR2 certificate accepted, promotion incomplete | yes | validate root proof, fetch exact approved bytes, resume cache promotion; no new generation |
| CR3 promotion present, input commit absent | no certified possibility | invariant violation/quarantine: valid issuance required pre-existing input commit; directory is not proof |
| CR4 input commit complete, push absent | pending only | independently certify pending if approved; resume governed push; no terminal claim |
| CR5 push complete, terminal absent | yes | inspect durable accepted push/task/chain, independently authorize exact terminal; never use latest to guess |
| CR6 terminal accepted, checkpoint absent | yes / finalization incomplete | reconstruct snapshot only from exact rooted facts, persist binding; T stays genuine, completion limb pending |
| CR7 checkpoint bound, receipt absent | yes / evidence incomplete | recover actual completion evidence, bind new observed receipt; never fabricate transport success |
| CR8 receipt bound, notification absent | yes | verify T, issue durable intent and one supported idempotent send; failure/unknown explicit |
| CR9 send possibly occurred, acknowledgement absent | conditionally | provider query/idempotency required; otherwise UNKNOWN/durable failure, no automatic resend |
| CR10 process crash/retry | yes with durable facts | resolve manifest-bound root request ID; reuse accepted event, otherwise remain incomplete |
| CR11 duplicate identical retry | yes | return identical certificate/terminal/delivery identity; no new sequence/report |
| CR12 same ID changed manifest or forked tail | no automatic resume | conflict/quarantine; do not allocate around failed CAS or erase accepted history |

Trust vocabulary: certified/current, certified/historical,
legacy-reconstructably-bound, legacy-provenance-incomplete, untrusted,
conflicting, ambiguous. Reconciliation vocabulary: clean_certified,
clean_with_certified_history, legacy_compatible_provenance_incomplete, conflict,
ambiguous, untrusted. Legacy vocabulary: LEGACY-A/B/C/D. No result/classifier
production API exists; no evidence is upgraded to certified provenance.

## Attack applicability

No attack closure is claimed. Structural/graph rows are potentially fully
testable in a future completed Slice1, but NOT exercised by a nonexistent model.
Current diagnostics inventory all 32 rows and prove only digest underspecification.
Columns explicitly separate applicability from actual coverage.

| Row | Frozen attacker action | Potential Slice1 scope | Actual coverage / deferment |
|---|---|---|---|
| 1 | forged pending report | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 2 | copied other-phase report | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 3 | same-phase forged report | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 4 | forged terminal report | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 5 | forged checkpoint | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 6 | forged report + checkpoint | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 7 | legitimate receipt replay | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 8 | copied receipt | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 9 | forged receipt | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 10 | notification replay | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 11 | malformed latest | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 12 | forged latest | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 13 | forged higher sequence | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 14 | predecessor substitution | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 15 | branch insertion | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 16 | chain cycle | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 17 | skipped predecessor | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 18 | terminal certificate replay | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 19 | issuance certificate replay | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 20 | cross-phase certificate | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 21 | cross-task substitution | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 22 | report mutation after cert | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 23 | certificate mutation | Structural/graph partial; rooted provenance still deferred | Deferred; no implemented model / no closure |
| 24 | crash before certificate | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 25 | crash after cert before input commit | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 26 | crash after push before terminal | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 27 | duplicate finalization | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 28 | mtime manipulation | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 29 | filename-order manipulation | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 30 | symlink/path/TOCTOU substitution | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 31 | incomplete trust reported complete | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |
| 32 | legacy provenance fabrication | Root/writer/consumer/final IV | Deferred; no implemented model / no closure |

## Disposition

Fresh readiness95 + N17 + L127 + M63 + J35 + K37: 374 passed in10.71s.
Relevant report/trust/CLI/reconcile/transition/finalization/notification/task/
bootstrap/filename selection: 582 passed,1 existing skip in36.63s.
Total selected956 pass/1 existing skip; no skip/xfail/delete introduced.
Task doctor282 pre-existing warnings/0errors. Check passed, health healthy,
status coherent. Normal completion runs the actual transition validator later.
Fresh fixed-candidate Fast Green is required before canonical completion;
this frozen evidence does not preclaim its result or a future commit hash.

Canonicalization, certificate digest derivation, parser, chain validator,
terminal-declaration validator, legacy classifier, recovery-state validator and
structured model/error APIs: NOT IMPLEMENTED. No side-effect-bearing new
production module exists, so AST/import audit and performance tests are N/A,
not pass claims. Existing production source delta is ZERO. Contract delta ZERO.
All 17 fields, 13 wire kinds / 11 architectural domains, 12 recovery descriptions,
26 requirements, 12 invariants and 32 attack rows are mechanically inventoried.

No root resolution/deployment, accepted-event access/provider authentication,
issuance/persistence, lifecycle consumer integration, cutover, migration, root
provisioning or historical mutation. Root references remain unresolved; model
possession would convey no authority. J/K witnesses must remain live.
Runtime Observed / observe / unavailable. N-16-5 OPEN; N-16-6/N-16-7 untouched.
Recognition-core IV ON HOLD. Fresh regression and Fast Green outcomes are
recorded in this phase's canonical completion source after fixed-candidate runs.

HASH CONSISTENCY != PROVENANCE
structurally valid generation certificate != R6-verified generation provenance
legacy compatibility != retroactive provenance certification
future provenance mechanism modeled != current lifecycle defect closed
historical no-production-change assertion != permanent prohibition on future authorized production evolution
This Slice 1 does not deploy the R6 root, issue or persist generation certificates,
activate cutover, mutate historical provenance, or close Phase150J/K defects.
