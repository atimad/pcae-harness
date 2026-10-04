# GCP-001 — Lifecycle Generation Provenance Contract

Contract ID: GCP-001
Version: 1.0
Status: FROZEN TARGET ARCHITECTURE; NOT IMPLEMENTED; CUTOVER INACTIVE
Architecture: Phase 150L, docs/PHASE_150L_GENERATION_PROVENANCE_ARCHITECTURE.md
Schema family: gcp/1.0 (semantic wire schema frozen below; no production model).

## 1. Scope, meaning and independent boundary

GCP-REQ-001: This contract governs future report-generation issuance, chain
membership and terminal disposition, not report-conclusion correctness, human
runtime approval, writer capability, PB permission or external runtime execution.
PFR-001 still governs content; PFN-001 still governs delivery. Their mandatory
sections and historical guarantees are unchanged. Content-complete and
provenance-complete SHALL be separate assessments. No implementation, deployment,
root installation, certificate issuance or historical migration occurs in 150L.

GCP-REQ-002: Select exactly one model: R6, a protected repository-transition
root plus a create-only event/certificate ledger. The root is NOT the report
directory, local Git, ordinary origin/main, a Python validator return value or
a locally written ledger. It is an independently administered accepted-event
history, published by an isolated lifecycle issuer to a protected repository
reference. A trusted, out-of-band root configuration pins provider/repository
identity, ledger reference, genesis, epoch, approved validator/publisher policy
and independent authorization domain. A report/caller SHALL NOT supply or
replace that configuration. Ordinary agent credentials SHALL NOT append to,
rewrite, delete, reconfigure or bypass protection of the root reference.

GCP-REQ-003: The issuer SHALL run approved policy, NOT proposed repository code.
An independently authenticated reviewer authorizes an exact event manifest:
repository/epoch, phase instance, canonical phase ID, task ID, approved input
commit/tree and metadata blob, report-pair digests, role, predecessor and intent.
Reviewer/publisher credentials and authorization-channel state SHALL be outside
the ordinary agent/same-process read/write domain. A broad phase grant, ordinary
client token, local acceptance result or certificate-shaped bytes is insufficient.
The issuer checks the independent authorization, canonical task/phase transition,
input object availability, full report trust and compare-and-swap expected tail.
It then durably appends the accepted event and certificate. This accepted event
is the governed issuance event; this does NOT authenticate a particular local
Python stack frame or prove that its report's technical conclusion is correct.

GCP-REQ-004: The acceptance proof SHALL verify both protected-reference ancestry
and provider-authenticated publication/authorization evidence for the exact event.
A Git author string, hash, branch name or unsigned local approval JSON is NOT
publication provenance. Current selection requires a fresh authenticated root
head and non-rollback check against the last independently validated root head.
Offline inclusion may establish historical membership only; it cannot assert
live currency. Root administrator/provider compromise is an explicit root threat,
not solved by GCP. Substitution of local root configuration is in scope and fails.
No HPAC, HATP, FIDO/YubiKey or PB authority is imported or repurposed.

## 2. Normative invariants

GCP-INV-001: Content digest proves byte identity, not governed issuance.
GCP-INV-002: Every post-cutover trusted generation requires a validated issuance
certificate anchored to the independently accepted lifecycle root.
GCP-INV-003: Every non-root generation has exactly one validated predecessor.
GCP-INV-004: Historical validity requires certified membership or explicit legacy class.
GCP-INV-005: Terminal status requires independent terminal certification.
GCP-INV-006: Checkpoint linkage cannot establish issuance by itself.
GCP-INV-007: Receipt linkage cannot establish issuance by itself.
GCP-INV-008: Notification marker never establishes terminal authority.
GCP-INV-009: Latest/current pointer never establishes provenance.
GCP-INV-010: Incomplete provenance cannot produce complete-trust status.
GCP-INV-011: Ambiguous chain or terminal state fails closed.
GCP-INV-012: Legacy compatibility never fabricates missing provenance.

## 3. Wire identity and closed schemas

GCP-REQ-005: Objects SHALL be JSON objects with exactly the fields below, no
duplicate keys, no NaN/nonfinite numbers, integers excluding booleans, UTF-8
strings and explicit null where allowed. Unknown schema/fields/roles fail closed.
Canonical certificate/event bytes use RFC-8785-compatible canonical JSON;
identities use full SHA-256 and full Git object IDs with explicit object format.
No truncated prefix matches. Payload identity binds the EXACT stored JSON and
Markdown bytes separately; lossy re-rendering is not identity. JSON SHALL be
fully assessed under PFR and applicable lifecycle trust, not its stored claim.
Certificate IDs hash the domain-separated canonical body, excluding their own
ID and detached anchor proof. A containing repository commit ID is in the
detached proof, NOT inside the body it contains: no self-reference cycle.

### 3.1 GenerationCertificate (gcp-generation/1.0)

| Field | Type | Class | Proof purpose |
|---|---|---|---|
| schema | literal gcp-generation/1.0 | identity | interpretation/version domain |
| root_epoch | opaque root-assigned string | provenance | one independently bootstrapped root epoch |
| repository_id | pinned provider repository identity | provenance | prevents other-repository substitution |
| phase_instance_id | root-assigned opaque string | identity | distinguishes a granted phase occurrence |
| phase_id | CPIPC canonical string | identity | binds report and phase |
| task_id | canonical granted task ID | provenance | binds task record, independent of file move |
| sequence | nonnegative integer | ordering | root assigns by CAS; not caller authority |
| generation_id | canonical tuple [root_epoch,phase_instance_id,sequence] | identity | phase-scoped collision/replay identity |
| role | pending or terminal_candidate | provenance | approved role; issued is not terminal |
| report_json_sha256 | full digest | identity | exact JSON bytes |
| report_markdown_sha256 | full digest | identity | exact published Markdown bytes |
| predecessor_certificate_id | digest or null | ordering | exactly one prior issuance; null only sequence zero |
| input_commit | {object_format,oid,tree_oid} | provenance | approved pre-existing input objects |
| completion_metadata_sha256 | digest | identity | binds the reviewed lifecycle input metadata |
| authorization_event_id | root event ID | provenance | independent exact-manifest approval |
| issuance_event_id | root-assigned event ID | provenance | durable accepted issuance event |
| certificate_id | domain-separated digest | identity | byte identity, not an authority token |

No time, filename, issued_by string, mutable seal or secret constructor is a
trust field. Root event time/producer are audit attributes only. Certificate
possession grants no authority and is never sufficient for validated membership.

### 3.2 TerminalCertificate (gcp-terminal/1.0)

GCP-REQ-006: Exact fields: schema, root_epoch, repository_id, phase_instance_id,
phase_id, task_id, generation_certificate_id, terminal_event_id,
authorization_event_id, task_completion_event_id, accepted_push_event_id,
validation_evidence_manifest_sha256, certificate_id. Identity/provenance types
are as above. Every reference resolves to the SAME granted phase/task/epoch;
the generation role MUST be terminal_candidate. The validation manifest binds
full content trust, test/governance evidence and the selected policy versions;
it is independently approved input, not a caller's boolean. The accepted push
event verifies the input candidate commit at the configured canonical code ref,
including the required ancestry and no outgoing phase-code candidate. It does
NOT require the terminal certificate's future storage commit to contain itself.

### 3.3 RootEvent and detached RootAnchorProof

GCP-REQ-007: RootEvent exact fields: schema=gcp-event/1.0, repository_id,
root_epoch, event_id, event_sequence, previous_event_id, event_kind,
phase_instance_id, phase_id, task_id, subject_manifest_sha256,
authorization_event_id, expected_phase_tail_certificate_id, outcome,
policy_manifest_sha256, audit_time, audit_producer. outcome is accepted only
for an authoritative event; proposals/rejections never enter the accepted chain.
event_kind is one of bootstrap, open_phase, authorize_manifest, issue_generation,
observe_promotion, accept_push, complete_task, certify_terminal,
bind_checkpoint, bind_receipt, record_notification, close_delivery, activate_cutover.
Bootstrap and activate_cutover use null phase_instance_id/phase_id/task_id/tail;
all other events require phase/task values. previous_event_id is null ONLY at
bootstrap (event_sequence zero). expected_phase_tail_certificate_id is null
ONLY for bootstrap, activate_cutover, open_phase, and authorization/issuance of
the root generation; otherwise it identifies the accepted phase tail.
authorization_event_id is null ONLY for bootstrap and authorize_manifest,
whose independently authenticated provider authorization is instead bound in
the detached acceptance proof. Other accepted events reference their exact
accepted authorize_manifest event. Sequences are root-assigned monotone integers with
exact previous-event linkage; audit_time/producer are descriptive, never proof.
An accepted subject manifest freezes the event-specific inputs in §§4–8.

Detached RootAnchorProof exact fields: schema=gcp-anchor/1.0, repository_id,
root_epoch, root_genesis_oid, root_commit_oid, certificate_blob_oid,
certificate_id, publication_evidence_id, authorization_evidence_id.
It is a locator, not bearer authority. Validation obtains authenticated evidence
from the configured provider/root domain, verifies exact blob inclusion and the
entire accepted chain/policy. Arbitrary caller-provided proof paths are rejected.
Protected root append is atomic CAS against previous root and per-phase tail.
No self-hashed authorization or publication document can replace this boundary.

## 4. Issuance and pending birth

GCP-REQ-008: The ordinary CLI constructs a PROPOSAL and stages immutable report
bytes plus lifecycle input manifest. A governed candidate commit contains those
bytes and inputs, but not its own containing-commit hash. Local rendering or
commit alone is not issuance. Independent review approves the exact manifest
against canonical task/phase facts and scope. The isolated issuer validates
those objects and accepts a root event/certificate before canonical promotion.
Only the durable accepted root append is the birth of a certified pending
generation. The root may inspect approved candidate Git objects without advancing
the canonical code ref; any object transfer is an explicitly governed lifecycle
operation, not runtime permission. No parentless ad-hoc local ledger is accepted.

GCP-REQ-009: Pending means pre-canonical-code-push, NOT pre-any-commit and NOT
pre-provenance. Certification occurs after the proposal/input commit exists and
before canonical promotion. Certificate persistence/its containing commit is a
later root transaction and therefore acyclic. An extra file inserted before
acceptance has no approved manifest/certificate and is quarantined, never history.
The issuer SHALL NOT enumerate files and automatically certify whatever is found.

## 5. Chain, terminal and regeneration

GCP-REQ-010: One phase instance/task/epoch has one certified linear generation
chain, one root generation and consecutive sequences starting at zero. Every
successor references the exact previous issuance certificate, payload identity
and approved transition intent through its subject manifest. Root CAS allocates
sequence; forged larger values, gaps, cycles, forks and cross-task/phase/epoch
links fail closed. Identical request ID plus identical manifest is idempotent;
same request ID plus different manifest conflicts. Caller IDs cannot select tail.

GCP-REQ-011: Multiple pending generations and a third pre-terminal generation
are allowed only through independently accepted successors. A pending generation
may be superseded by a terminal_candidate. Terminal certification occurs only
after independently accepted push and completed task events and full trust checks.
The terminal issuer atomically binds the chain tail to exactly one TerminalCertificate.
Checkpoint/receipt are outputs/evidence of that transition, not its circular root.

GCP-REQ-012: v1.0 forbids new generations after terminal certification. Notification
requires that terminal certification, so no ordinary post-notification regeneration
is supported. Re-entry returns the identical existing terminal and resumes delivery;
it never creates a replacement report. All pushed-status/commit-list synchronization
must finish BEFORE terminal candidate bytes are frozen. Corrections after terminal
require a separately governed successor phase recording the correction, not silent
same-phase replacement. Future amendment topology needs separate contract evolution.

## 6. Checkpoint, receipt, notification and latest

GCP-REQ-013: Checkpoint is a local recovery/progress snapshot and terminal output.
PREPARED checkpoints may exist before terminal certification but cannot select it.
Terminal checkpoint binding exact fields: schema=gcp-checkpoint-binding/1.0,
repository_id, root_epoch, phase_instance_id, task_id, terminal_certificate_id,
generation_certificate_id, checkpoint_sha256, checkpoint_event_id. Its root-bound
manifest identifies the checkpoint's immutable terminal snapshot; subsequent
progress is append-only evidence, not mutation of certified snapshot bytes.
Missing checkpoint is recoverable from independently durable certified facts,
but finalization remains incomplete until the required binding exists.

GCP-REQ-014: Receipt certifies NONE of issuance/terminal/chain directly. It records
the observed completion/delivery event for the already-certified terminal. Exact
binding fields: schema=gcp-receipt-binding/1.0, repository_id, root_epoch,
phase_instance_id, task_id, terminal_certificate_id, generation_certificate_id,
receipt_sha256, logical_delivery_id, delivery_purpose, receipt_event_id,
evidence_manifest_sha256. Root acceptance verifies actual durable evidence and
exact subject equality. A G1 receipt cannot validate G2. Completion observation
and transport API acceptance are distinct; neither proves user reading/approval.

GCP-REQ-015: Notification evidence binds exactly the sent generation, terminal
certificate, exact transmitted payload digest, purpose, sink and logical delivery
ID; provider receipts are explicit actual observations, not synthetic success.
Markers are derived idempotency evidence and may rotate. Historical notification
references remain valid only through verified event membership and subject equality.
Root accepted notification evidence or explicit durable delivery-failure evidence
fulfills the delivery limb; absence/unknown outcome never becomes a sent claim.

GCP-REQ-016: latest/current is a derived cache/index. It is never a selector/root.
Missing/stale index can be rebuilt only from a unique validated root terminal;
malformed/forged/path-substituted indexes are reported explicitly and quarantined.
Read-only reconcile does not silently rewrite them. A pointer to historical
content is not current. Rebuild is a governed operation and must preserve evidence.

## 7. Legacy compatibility, cutover and migration

GCP-REQ-017: Legacy classes disclose bounded facts, not new certificates:

| Class | Required evidence | Allowed operations | Forbidden claim |
|---|---|---|---|
| LEGACY-A | independently retained contemporary acceptance/closure evidence | display, audit, old-rule historical reconstruction with limitations | new issuance/terminal certification |
| LEGACY-B | independent canonical records bind listed bytes/observed relationships | additionally reconstruct EXACT listed facts, citing source commit and observation time | inferred unrecorded issuance, time or approval |
| LEGACY-C | bytes/history exist but no sufficient independent binding | display/audit as provenance-incomplete; no strong current selection | complete trust |
| LEGACY-D | contradictory bindings, tampering, unsafe paths or failed required validation | quarantine/audit conflict evidence only | trusted historical/current selection |

A and B may coexist as evidence dimensions; primary class B may certify only
the expressly listed historical FACTS, never generation provenance. A/B still
have legacy-provenance-incomplete for new-generation trust. C is the conservative
default, D overrides other classes on proven conflict. Legacy terminal display
is a named audit-only compatibility operation, never certified/current selection.
Later inventories establish observations at their own time, not past issuance.

GCP-REQ-018: Select C1+C4: mandatory new-write certification for phase instances
opened after one independently accepted CutoverActivation; dual-read explicit
legacy classes. Cutover manifest freezes schema/policy versions, approved
implementation/IV evidence, independently bootstrapped root configuration and
the pre-cutover phase-instance set from accepted canonical history. Artifact
timestamps, missing certificates, user metadata or feature flags cannot choose
legacy mode. Unknown instances fail closed. All phases before activation,
including 150L, remain legacy; architecture freeze is NOT activation.

GCP-REQ-019: NO MIGRATION is required for historical reports. An optional derived
observation index may record only independently provable facts, explicitly
non-certifying and never a root. Do not rewrite old report/cp/receipt/marker bytes
or fabricate certificates. Any later demand for stronger historic trust requires
separate migration architecture; unprovable facts cannot be migrated into truth.

## 8. Trust, rehydration, reconcile and recovery

GCP-REQ-020: Trust vocabulary SHALL distinguish certified/current,
certified/historical, legacy-reconstructably-bound, legacy-provenance-incomplete,
untrusted, conflicting and ambiguous. Complete trust requires content checks,
validated rooted issuance/terminal/chain, independently accepted task/push facts,
and all required completion/delivery evidence limbs. Schema validity alone cannot
set complete trust. Terminal provenance and delivery completeness are separate axes.

GCP-REQ-021: Backward-compatible result extension retains existing status fields
as mechanical consistency results, adding schema=gcp-result/1.0,
provenance_state, complete_trust, legacy_class, reconciliation_class,
proof_references and limitations. reconciliation_class is clean_certified,
clean_with_certified_history, legacy_compatible_provenance_incomplete, conflict,
ambiguous or untrusted. Old status='reconciled'/exit 0 is NOT strong certification.
Post-cutover authoritative lifecycle consumers MUST require complete_trust and
certified/current; old consumers receive a conspicuous legacy limitation warning.
No new runtime authority consumer is created.

GCP-REQ-022: Rehydration discovers safely (no symlink/traversal/TOCTOU replacement),
checks exact bytes and full report trust, obtains the independent root head,
resolves exact issuance proofs, reconstructs one linear certified chain, classifies
legacy separately, rejects forks/cycles/gaps, verifies unique terminal event and
task/push bindings, then checkpoint/receipt evidence. Notification is separate
delivery evidence. Only then derive current; pointers never steer selection.
Missing mandatory proof, malformed root, branch ambiguity or invalid signature/
provider publication evidence fails closed; no 'pick the candidate that passes'.

GCP-REQ-023: Reconcile checks certified chain, terminal, checkpoint/receipt exact
bindings and notification/index state separately. It returns the six distinct
reconciliation classes above; legacy compatibility is never clean_certified.
Genuine missing optional legacy notification is disclosed, not synthesized.
Accepted extra historical evidence must be in the root chain or explicitly
legacy; directory insertion cannot expand either set. Unlinked objects are
rejected/quarantined and cannot downgrade a certified phase to legacy.

GCP-REQ-024: Recovery uses durable independently validated evidence only. The
crash table in the architecture is binding. Root CAS and manifest-bound request
IDs make retries idempotent. No automatic rollback erases an accepted event;
failed proposals remain quarantined. Lost report bytes can be fetched from an
approved immutable input object ONLY when all exact digests match; a digest
alone cannot reconstruct content. No delivery success may be inferred from
intent. If provider idempotency/query is unavailable after an ambiguous send,
record UNKNOWN/durable failure and stop automatic resend for governed recovery.

## 9. Implementation and non-goals

GCP-REQ-025: Implementation SHALL be sliced with independent verification after
each security-significant slice. Slice 1 is pure schema-backed models and pure
validation of caller-supplied proof DATA, with no lifecycle writes or authority
resolution. Root deployment/provisioning/activation requires separate explicit
authorization and verified isolation. If isolation cannot be deployed, cutover
is BLOCKED; do not fall back to ordinary main, in-process seals or a local signer.
Existing validators/CLTR may inform checks but are not silently promoted to roots.

GCP-REQ-026: Preserve all semantic walls: HASH CONSISTENCY != PROVENANCE;
FILE LOCATION != TRUSTED ORIGIN; STRUCTURALLY VALID OBJECT != TRUSTED CANONICAL STATE;
promoted generation != governed-issued generation; generation digest != generation
provenance; predecessor digest != predecessor authorization; checkpoint match !=
terminal provenance; receipt match != terminal provenance; notification marker !=
authority; latest pointer != provenance; latest pointer != terminal proof;
historical generation != automatically trusted; terminal claim != terminal proof;
complete structure != complete trust; receipt = evidence != authority;
legacy compatibility != retroactive provenance certification.
Runtime remains Observed / observe / unavailable. No HPAC/helper/foundation,
HATP/PB/POL changes; N-16-5 OPEN; N-16-6/N-16-7 untouched.

## 10. Freeze and traceability

Phase 150L freezes this TARGET model, not its implementation or readiness.
GCP-REQ-001–026 and GCP-INV-001–012 trace to the architecture's model matrix,
root boundary, event/field tables, attack matrix, compatibility/cutover and
crash/retry analysis. Changes to proof, roles, root isolation, topology or
cutover require governed revision and independent verification; no implicit
field/schema drift. PFR-001 structure, GLP-001 sequencing, PFN-001 delivery,
and existing FGSC-001 attribution remain unchanged.
