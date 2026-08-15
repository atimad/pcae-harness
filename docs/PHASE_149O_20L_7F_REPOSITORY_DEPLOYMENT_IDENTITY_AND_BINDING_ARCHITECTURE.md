# Phase 149O.20L.7F — Repository/Deployment Identity + DeploymentBinding Architecture

## 0. Status

**Architecture/design only.** No `.pcae/repository-identity.json` created. No `DeploymentBinding` created. No repository onboarded. No Dell mutation. No production source (`src/pcae/**`), CLI, schema, or contract modified. Boundary C, Boundary A, HATP activation, Cutover Record, and Permission Broker all remain untouched and **NOT AUTHORIZED**.

**Phase entry commit:** `a5ad8573` (`Phase 149O.20L.7E: task lifecycle transitions (close to idle)`), `origin/main` == `HEAD`, 0 commits ahead, working tree clean at entry.

**Reconciliation:** `pcae phase-report reconcile --phase-id 149O.20L.7E` → `reconciled`, 2 generations promoted, marker `already_dispatched`, mutation `none`. No prior-phase artifact was altered by this phase.

## 1. Purpose and Method

Phase 149O.20L.7E independently measured the live Dell deployment as `NON_COMPLIANT`, failing set exactly `{HBDC-REQ-042}`, immediate reason `no_repository_identity_present`, with an empty trust store (`/etc/pcae/hatp/trust-store`, zero files — no `DeploymentBinding` of any kind). This phase does **not** treat "create a DeploymentBinding" as the next correct action. It reconstructs, entirely from primary sources (contracts, production source, the governing CHGR, and prior architecture docs — never from task/TODO prose), the full chain of concepts between "no repository identity present" and "Boundary C certified, Boundary A active": repository identity, DeploymentBinding, their authority relationship, their creation mechanisms (or absence), their relationship to onboarding and to certification, and the exact next governed step.

All entry-check commands from the governing prompt were run this phase (§3 below) and are reflected throughout.

## 2. Entry Checks (this phase, read-only)

```
git status --short                    -> (clean)
git status --branch --short           -> ## main...origin/main
git rev-list --count origin/main..HEAD -> 0
pcae health                           -> healthy, git status clean
pcae check                            -> passed
pcae status coherence                 -> coherent
pcae doctor task-memory               -> warnings (pre-existing: historical
                                          tasks/done/ entries predating this
                                          phase, missing from tasks/DONE.md;
                                          unrelated to this phase's scope,
                                          not remediated here)
pcae push check                       -> clean (nothing_to_push)
pcae runtime inspect                  -> Observed / observe / unavailable
pcae notify status                    -> telegram configured/enabled/ready
pcae phase-report show --latest       -> 149O.20L.7E canonical report, consistent
pcae phase-report reconcile --phase-id 149O.20L.7E -> reconciled, mutation none
```

No Dell SSH session was opened this phase. Dell state (Boundary-P provisioning, trust-store emptiness, repository-identity absence) was independently, freshly established by 149O.20L.7E on the same day this phase runs; re-deriving it from a second live session would add no new evidence and this phase's scope is architecture reconstruction from primary source, not a third independent Dell verification. This is stated explicitly rather than left implicit.

## 3. Terminology Freeze (existing canonical names — none invented)

| Term | Canonical source | Meaning |
|---|---|---|
| `repository_instance_id` / `RepositoryIdentity` | `src/pcae/core/repository_identity.py`; HATP-001 §17 (HATP-REQ-046..051); CRI architecture (149O.1B.2 §9) | **CRI Model A, Layer 1.** A repository-local, randomly generated (UUID4), persisted identifier. Agent-readable and agent-writable. Confers no authority by itself (HATP-REQ-051, HBDC-REQ-042, CBD-5). |
| `DeploymentBinding` | `src/pcae/core/hatp_bootstrap.py` (`DeploymentBinding` dataclass, `HATPTrustStore`); HATP-001 §18 (HATP-REQ-052..063); HBDC-001 §16 | **CRI Model A, Layer 2.** An admin-owned, agent-unwritable record inside the HATP Protected Root's trust store binding `repository_id -> canonical_deployment_root -> principal_id/signer_key_id/provider_profile -> authority_scope -> status`. The controlling authority artifact (HBDC-REQ-042). |
| `canonical_deployment_root` | `hatp_bootstrap.resolve_canonical_deployment_root()` | Deterministic, symlink-resolved, absolute-path canonicalization of a local deployment root. Compared byte-for-byte inside `deployment_binding_matches()`. |
| Protected Root | `HATPTrustStore.production()` / `_default_production_trust_root()` | Existing concept, unmodified. Fixed platform path (`/etc/pcae/hatp/trust-store` on Linux); admin-owned; agent-unwritable; holds the `DeploymentBinding` registry. |
| CRI Model A | 149O.1B.2 §9 | The two-layer identity model this whole architecture already committed to: Layer 1 (repository-local, non-authoritative) + Layer 2 (admin-owned, authoritative, canonical-root-bound). |
| "Repository" (in HBDC-REQ-042's current wiring) | `hatp_class_b_conformance._check_deployment_identity` | As currently wired, **the PCAE runtime's own deployed source checkout** (the Model-A canonical repository working tree PCAE itself executes from) — not a separate, future "managed application repository." See §9.

No `DeploymentIdentity`, `ManagedRepositoryRoot`, or other new vocabulary is introduced. None is needed: every question the governing prompt poses is already answered by an existing canonical name.

## 4. HBDC-REQ-042 — Exact Normative Text and What It Protects

Recovered verbatim from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` §16:

> **HBDC-REQ-042.** `repository_instance_id` (CRI Layer 1, repository-local and agent-writable per HATP-001 §17) confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding` (CRI Layer 2).

This is bound to security invariant **CBD-5**: "Identifier mutation alone (`repository_instance_id`) cannot confer authority." HBDC-REQ-008 independently designates `.pcae/repository-identity.json` as the named exception to the agent-write prohibition (HBDC-REQ-007) — explicitly agent-writable **and** explicitly non-authoritative, in the same clause as `.pcae/hatp-evidence/`.

**What REQ-042's text literally asserts** is narrower than what the *production verifier* checks under REQ-042's ID. The contract text is a negative security statement ("identity alone confers nothing"); it does not, by itself, mandate "identity SHALL be present." The production verifier (§5 below) implements a stronger, positive check — identity present AND a matching active binding present — under the same requirement ID. This is a real but non-blocking gap worth naming precisely (Finding F1, §29): the contract's normative text and the verifier's operational semantics are related but not textually identical; a future contract-freeze phase should either add an explicit "SHALL require both repository identity and an active matching DeploymentBinding to be present for COMPLIANT" requirement, or the verifier's docstring should cite exactly the contract clause it operationalizes. Neither the contract nor the verifier is wrong; the mapping between them is implicit rather than 1:1 textual.

**Ordering/host-migration siblings**, also §16: HBDC-REQ-043 (worktrees need independent binding), HBDC-REQ-044 (clones/copies need independent binding), HBDC-REQ-045 (host migration needs new binding + recertification), HBDC-REQ-046 (cross-host/path restore does not retain authority). Repository identity and DeploymentBinding are both explicitly referenced; both are independently mandatory (§9 below formalizes why); certification is referenced only via HBDC-REQ-045's "recertification" language (host migration invalidates both binding and certification); Protected Root is referenced implicitly (DeploymentBinding lives there); host identity is **not** referenced anywhere in §16 — the binding key is `(repository_id, canonical_deployment_root)`, not `(repository_id, machine_id)` (§16 below).

## 5. REQ-042 Verifier Call Path (production, exact)

`src/pcae/core/hatp_class_b_conformance.py::_check_deployment_identity(root)`:

```
1. canonical_root = hatp_bootstrap.resolve_canonical_deployment_root(root.path)
     fails -> HBDC-REQ-042 False, "canonical_deployment_root_unresolvable"
2. identity = repository_identity.read_repository_identity(root)
     malformed -> HBDC-REQ-042 False, "repository_identity_malformed"
     absent    -> HBDC-REQ-042 False, "no_repository_identity_present"   <- 7E's observed reason
3. store = hatp_bootstrap.HATPTrustStore.production()
   binding = store.load_repository_enrollment(identity.repository_instance_id)
     trust store unreadable/malformed -> HBDC-REQ-042 False, "trust_store_unavailable"
4. matches = hatp_bootstrap.deployment_binding_matches(binding,
                 repository_id=identity.repository_instance_id,
                 canonical_deployment_root=canonical_root)
     no match -> HBDC-REQ-042 False, "no_active_deployment_binding_matches_repository_and_root"
     match    -> HBDC-REQ-042 True,  "deployment_binding_matches_repository_and_root"
```

**Complete failure-reason vocabulary for HBDC-REQ-042** (production source, exhaustive — six terminal outcomes, five failing):

1. `canonical_deployment_root_unresolvable`
2. `repository_identity_malformed`
3. `no_repository_identity_present` — 7E's live observed reason
4. `trust_store_unavailable`
5. `no_active_deployment_binding_matches_repository_and_root`
6. `deployment_binding_matches_repository_and_root` (only `True` outcome)

**Evaluation order is architecture-bearing, exactly as the governing prompt anticipated (§6 of the prompt):** canonical-root resolution happens first (step 1), then repository-identity lookup (step 2), and **only if identity is present** does the code proceed to trust-store/binding lookup (steps 3-4). On the live Dell host, execution stopped at step 2 — `deployment_binding_matches()` was never reached, and the trust store's own emptiness (independently confirmed by 7E) was never actually exercised by this code path on that run. Both facts (identity absent, trust store empty) are true independently, but only the first was the *proximate* cause of the observed reason string. This ordering means: **repository identity is a hard prerequisite gate before binding-matching logic is even reached** — you cannot observe `no_active_deployment_binding_matches_repository_and_root` until repository identity already exists.

`deployment_binding_matches()` (`hatp_bootstrap.py`) additionally requires `binding.status == "active"` — a `revoked` or otherwise-non-`"active"`-status binding is treated identically to no binding at all (§21 below).

## 6. Repository-Identity Artifact — Reconstruction

`src/pcae/core/repository_identity.py`, `RepositoryIdentity` dataclass, `SCHEMA_VERSION = 1`:

```json
{
  "schema_version": 1,
  "repository_instance_id": "<uuid4>",
  "created_at": "<ISO-8601 UTC, millisecond precision, 'Z' suffix>"
}
```

- **Canonical path:** `.pcae/repository-identity.json`, repository-root-relative.
- **Producer:** `ensure_repository_identity(root)` — idempotent-preserve (returns existing valid identity unchanged; generates+atomically writes only if absent; **raises** `RepositoryIdentityMalformedError` and refuses to touch the file if it exists but is invalid — never silently regenerates).
- **Consumers (production):** `hatp_class_b_conformance._check_deployment_identity` (read-only, via `read_repository_identity`); `hatp_mandatory_certification.py` (certify-time derivation, HMIC-REQ-043); `hatp_mandatory_cutover.py` (via the conformance aggregator). `repository_identity.py` is itself one of HMIC-001's 28 frozen canonical files (§17 below) — its own bytes participate in `implementation_scope_digest`.
- **Persistence model:** plain JSON file, atomic write (`tempfile.mkstemp` in the same directory, `fsync`, `os.replace`), symlink-rejecting on both the target and its parent, both before and after the write race window.
- **Trust level:** explicitly **non-authoritative** (HATP-REQ-051, HBDC-REQ-008). Repository-local, agent-writable, not a secret, not a trust root (HATP-REQ-049).
- **Digest/self-binding:** none. The file carries no signature, no HMAC, no binding to a certification digest. Its only internal integrity control is closed-schema validation (`validate_repository_identity_document` rejects unknown fields, wrong `schema_version`, non-UUID4 IDs, non-ISO-8601 timestamps) — this catches corruption/malformation, not forgery.
- **Repository root relationship:** the file lives *inside* the repository it identifies (`<root>/.pcae/repository-identity.json`), which is exactly why it cannot be authoritative on its own (§8, copy/clone attack).
- **Production-supported, not merely assumed:** confirmed production, not conceptual. `pcae init` (`src/pcae/commands/init.py:42`) already calls `ensure_repository_identity(root)` on every `pcae init` invocation (non-dry-run). This directly falsifies any assumption that repository-identity creation is unimplemented — **it is implemented, tested (multiple test modules, e.g. `tests/test_repository_identity.py`), and wired into the one existing PCAE lifecycle command that plausibly owns it.**

## 7. Repository-Identity Creation Mechanism — Confirmed Present

Searched CLI (`src/pcae/cli.py`), core modules, tests, schemas, architecture docs. Result:

- **CLI:** `pcae init` → `run_init()` → `ensure_repository_identity(root)`. This is the sole production creation path. No dedicated `pcae repository identity ...` command family exists (§25).
- **Core:** `ensure_repository_identity()` (create-if-absent, fail-closed on malformed), `read_repository_identity()` (read-only), `validate_repository_identity_document()` (schema gate). No rotate, revoke, repair, import, or migrate function exists anywhere in `repository_identity.py` or elsewhere — only **create-if-absent** and **read**.
- **Tests:** extensive coverage across ~15 test modules (worktree-distinctness, malformed-refusal, idempotence, cross-repo distinctness, symlink rejection, etc.).

**Status: CREATE and READ exist. ROTATE, REVOKE, REPAIR, IMPORT, MIGRATE do not exist anywhere in production.** This is a materially different state than DeploymentBinding (§8) — repository identity has a real, tested, CLI-wired producer; DeploymentBinding has none.

## 8. DeploymentBinding — Schema, Consumers, and Producer Status

**Schema** (`hatp_bootstrap.py::DeploymentBinding`, frozen dataclass, validated by `_parse_deployment_binding` against a closed field set):

```
repository_id              (UUID4, matches a RepositoryIdentity.repository_instance_id)
canonical_deployment_root  (string, resolve_canonical_deployment_root() output)
principal_id                (string, non-empty)
signer_key_id                (string, non-empty)
provider_profile             (string, non-empty)
authority_scope               (string, non-empty)
valid_from                    (ISO-8601 timestamp, timezone-aware)
status                         ("active" | "revoked", closed vocabulary via _STATUS_VALUES)
revoked_at                    (required iff status == "revoked"; forbidden otherwise)
```

Persisted as one entry (keyed by `repository_id`) inside `registry.json` under the Protected Root's `deployment_bindings` array, alongside `principals`, `signers`, and `authorities` arrays in the same registry document (`_parse_registry_document`).

**Consumers:** `HATPTrustStore.load_repository_enrollment()`, `.resolve_deployment_authorization()`; `deployment_binding_matches()`; `hatp_class_b_conformance._check_deployment_identity` (HBDC-REQ-042); transitively, `hatp_mandatory_cutover.assess_hatp_mandatory_activation_readiness` (§10). All of these are **read-only** with respect to `DeploymentBinding`.

**Producer:** searched `HATPTrustStore` (all methods are lookups — `load_repository_enrollment`, `lookup_principal`, `lookup_signer`, `lookup_authority`, `resolve_deployment_authorization`, `environment_status`; **zero write methods**), all of `hatp_bootstrap.py`, the CLI, and all test modules. `HATPTrustStore`'s own class docstring states this explicitly: *"No method here mutates state (HATP-REQ-036-042: enrollment, revocation, and rotation are administrative-surface-only and are not implemented by this phase at all)."*

**CONSUMER EXISTS — PRODUCER ABSENT.** This independently reconfirms 7E's finding rather than merely repeating it: there is no `create_deployment_binding`, `enroll_deployment`, `register_binding`, or any CLI verb for `DeploymentBinding` anywhere in this codebase. The only way a `DeploymentBinding` can currently come into existence in production is an out-of-band, non-PCAE-agent, admin-authored edit of `registry.json` directly on the Protected Root — which is consistent with the trust model (HBDC-REQ-009: admin exclusively holds this write authority) but means **no governed, auditable, schema-validated creation flow exists today**, even for the admin principal.

## 9. Repository Identity Semantics

Repository identity (`repository_instance_id`) identifies **one specific local, on-disk deployment instance of a PCAE repository** — not the Git repository's lineage/history, not a PCAE "project" in the abstract, not a generated cross-host project UUID, and explicitly not a Git commit SHA (HATP-REQ-047 rules out deriving it from Git HEAD/object history, remote URL, or filesystem path alone). It is:

- **Not** Git repository lineage — a fork or clone gets its own, independent identity (149O.1B.2 §11 scenario matrix); identity does not follow "the same codebase," it follows "this one on-disk instance."
- **Not** a PCAE "project" concept in any cross-deployment sense — there is no field anywhere connecting two `repository_instance_id`s as "the same project on two hosts."
- **Not** host-independent in the sense of surviving a full copy — copying the repository (including the identity file) to a new path or host produces two on-disk instances sharing the same *value*, which is exactly the attack CRI Model A's two-layer design is built to survive by making the shared value irrelevant (§8 above; deployment authority is decided by Layer 2, not Layer 1).
- **Not** deployment-specific in isolation — the ID itself is deployment-*instance*-scoped (149O.1B.2 §14 explicitly rejected a separate `lineage_id`/`instance_id` split as unneeded complexity for v1), but *authority* over a given instance is what Layer 2 adds.

In short: **repository identity is a bare, non-authoritative instance label for "this particular checked-out directory tree"; DeploymentBinding is what turns a specific `(label, canonicalized physical location)` pair into an authorized deployment.**

## 10. Repository Identity Stability

From HATP-REQ-047 and 149O.1B.2 §11's scenario matrix (verified against current source, unchanged):

| Change | Repository identity (Layer 1) |
|---|---|
| New Git commit | unchanged |
| Branch switch | unchanged |
| Remote URL change | unchanged |
| Path rename / move (same host) | **preserved** — the file moves with the directory |
| Clone to another host | fresh clone gets **no** identity file (untracked, §12 below) until its own future `pcae init` |
| Fork | fork's own independent identity, once initialized |
| `pcae init` re-run (idempotent-preserve) | **preserved**, never silently regenerated |
| Repository repair (non-identity files) | unchanged |
| Migration (whole-tree copy to new host/path) | **preserved as a value** (copied verbatim) — but see §9: the copy does not inherit authority |
| Explicit re-identify (conceptual only, `pcae repository reidentify`-equivalent — not implemented anywhere in current source) | would generate a **new** ID and invalidate the old binding; not implemented |

## 11. Repository Identity Uniqueness

**Global uniqueness domain, by construction, not by registry.** `repository_instance_id` is a UUID4 (`is_valid_repository_instance_id` enforces version-4 format), generated locally via `uuid.uuid4()` with no central allocator, no collision registry, and no coordination with any other deployment. Uniqueness is probabilistic (UUID4 collision space), not administratively guaranteed — there is no PCAE-installation-wide or organization-wide registry that would even notice a collision. This is architecturally acceptable *only* because the identifier is explicitly non-authoritative (§9) — a UUID4 collision between two unrelated repositories would not confer authority across them, because Layer 2's canonical-root comparison is the actual authority gate (§8). **Path or hostname is never used as identity** (HATP-REQ-047 explicitly rules out path-only or remote-URL-only derivation) — confirmed unchanged in current source.

## 12. Repository Identity Authority (who may create it)

**No approval, election, or elevated privilege is required to create repository identity.** `ensure_repository_identity()` is callable by the ordinary agent OS principal — it is explicitly not authority-bearing (HATP-REQ-048: "identity creation alone grants no HATP authority... generation is not itself a sensitive operation and needs no human approval"). It is invoked automatically as a side effect of `pcae init`, which any repository operator (human or agent) can run. This is a deliberate architecture choice (149O.1B.2 §16), not an oversight: because Layer 1 confers nothing by itself, gating its creation behind human approval would be security theater without closing any real attack surface, while adding friction to ordinary onboarding. **Authority over a given identity (i.e., whether it means anything) is conferred exclusively by the admin principal's DeploymentBinding creation (§8, §21) — never by identity creation itself.**

## 13. Repository Identity Trust

A consumer (e.g. the REQ-042 verifier) does **not** trust the repository-identity file's *contents* as authoritative in any way — it only uses the value as a lookup key into the actually-trusted Layer 2 registry. The file's own integrity protections are: closed-schema validation (rejects malformed documents outright, `RepositoryIdentityMalformedError`, never silently repaired), symlink rejection on read and write, and atomic-write crash-consistency. It has **no** digest, provenance record, governance record, or source-control status of its own (§14 below explains why that is correct, not a gap). Because it is repository-local and agent-writable by design, **it is explicitly and by contract acceptable that a repository writer can alter it (HBDC-REQ-008)** — the architecture's answer to "is that acceptable?" is unambiguously **yes**, precisely because no production consumer treats it as authoritative; every consumer that cares about authority additionally checks Layer 2.

## 14. Repository Identity and the One-Repo/One-PCAE-Project Model

The product model ("one repository -> one independently governed PCAE project") is supported as follows, derived from CRI Model A's own decisions (149O.1B.2 §9/§13):

- **Each onboarded repository instance gets exactly one repository identity** (Layer 1), created idempotently on first `pcae init`.
- **The identity does *not* automatically follow clones/deployments** — a `git clone` produces a fresh checkout with no identity metadata at all (149O.1B.2 §12 verified this is *not* globally gitignored by default in this repo's conventions, and explicitly requires any future repository-identity file to be added to VCS-ignore — see §15 below for the current gap this leaves).
- **Each independent deployment (including worktrees, per HATP-REQ-060) gets its own identity and, if HATP-authorized, its own separate DeploymentBinding.** One repository lineage can therefore have many independent on-disk instances, each independently identified and independently (or not) bound — this is exactly the "one repo -> one project, but N independently governed deployments of it" shape the product model implies, and it is what makes DeploymentBinding, not repository identity, the actual unit of "is this deployment authorized."

## 15. Repository-Identity File — VCS-Ignore Status (verified, not assumed)

149O.1B.2 §12 flagged as a binding future requirement that a repository-instance identity file "must not be committed to Git" and that "any future implementation phase must add this file to VCS-ignore rules as part of its own scope." Checked directly this phase:

```
$ cat .pcae/.gitignore | grep repository-identity
repository-identity.json
```

**`repository-identity.json` is already listed in `.pcae/.gitignore`.** The implementation phase that added `repository_identity.py` (149O.1E) discharged 149O.1B.2 §12's obligation. This repository's own working tree confirms it: `.pcae/repository-identity.json` does not exist locally (never initialized on this Mac clone) and `git check-ignore -v .pcae/repository-identity.json` reports it as ignored. **No gap here — resolved, not merely assumed.**

## 16. Repository Onboarding Boundary

Dell's Boundary-P provisioning (149O.20L.7E, independently reconfirmed) established `/opt/pcae/projects` as an **empty container directory** — no `/opt/pcae/projects/<repo-slug>/repo` exists. Repository onboarding (populating that structure with an actual managed application repository) was intentionally excluded from Dell provisioning scope.

**Can a valid repository identity exist before an application repository is onboarded? — Yes, but it is not relevant to closing HBDC-REQ-042.** Repository identity is created by `pcae init` run *against a specific repository working tree*. The tree that matters for HBDC-REQ-042, as currently wired (§17 below), is the **PCAE runtime's own deployed source checkout** at `/opt/pcae/runtime/src` — which already exists and is already a real Git working tree (HEAD `28bf137b...`, detached, clean). Repository identity *for that tree* does not require `/opt/pcae/projects/<repo-slug>/repo` to exist at all. **HBDC-REQ-042, as currently wired, is therefore not blocked by the onboarding gap** — it is blocked purely by nobody having run `pcae init` (or equivalently, `ensure_repository_identity`) against `/opt/pcae/runtime/src` yet, and by no `DeploymentBinding` existing regardless.

This is stated as a specific, evidence-based conclusion, not a general claim that onboarding is irrelevant to all future HBDC-related work — see §17-18 for the important caveat this creates.

## 17. Which Repository Is Action 9 Actually Evaluating? (resolved, not assumed)

Recovered verbatim, byte-for-byte, from the governing CHGR's own bound rationale text (149O.20L.7E §27, independently reconstructed again this phase from the same primary source — `.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json`):

```
sudo -u pcae sh -c "cd /opt/pcae/runtime/src && env -i \
  HOME=/home/pcae PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1 \
  /opt/pcae/runtime/venv/bin/python3 -c '
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
result = verify_class_b_deployment_conformance()
print(result.status.value)
...'"
```

`verify_class_b_deployment_conformance()` is called with **no argument**. Its signature (`hatp_class_b_conformance.py:135-137`):

```python
def verify_class_b_deployment_conformance(root: Optional[HarnessPath] = None) -> ...:
    if root is None:
        root = HarnessPath.cwd()
```

With `CWD=/opt/pcae/runtime/src` (set explicitly by the invocation's `cd`, not by the launcher wrapper — the wrapper's own fixed CWD is `/opt/pcae/runtime`, a different, enclosing directory), `root` resolves to `/opt/pcae/runtime/src`.

**Answer: Action 9, as actually invoked, evaluates the PCAE runtime's own deployed source checkout — the same directory tree that Model A (HBDC-REQ-022) already requires PCAE's authority modules to execute from.** It is not evaluating, and currently has no path to evaluate, a hypothetical future managed project repository under `/opt/pcae/projects/<repo-slug>/repo`. This is not an accident of the specific invocation; it falls directly out of Model A's own definition: under Model A, "the repository" and "the runtime's own working tree" are architecturally the *same directory*, by contract (HBDC-REQ-022: "PCAE authority modules execute from the canonical repository working tree via editable install"). There is currently no second, distinct "managed application repository" concept wired into HBDC-REQ-042 at all — that concept exists only in the phase-entry framing and in `/opt/pcae/projects`' directory-naming convention, neither of which HBDC-REQ-042's verifier code references.

## 18. Runtime-Source vs. Managed-Repository Distinction

- **PCAE runtime source checkout:** the Git working tree PCAE's own authority-bearing modules execute from (`/opt/pcae/runtime/src` on Dell). Model A requires this to be an editable install of the canonical `pcae-harness` repository itself.
- **Managed application repository:** a distinct, hypothetical future repository that PCAE would govern/operate *on behalf of a separate project* (the `/opt/pcae/projects/<repo-slug>/repo` convention). No architecture, contract, schema, or code today defines what identity/binding relationship such a repository would have to PCAE, to HBDC-REQ-042, or to the runtime checkout.
- **Repository identity owner:** currently, only the runtime checkout can plausibly own one, because `ensure_repository_identity` operates on whatever `root` a caller supplies, and the only caller in the actual Action-9 invocation supplies (implicitly, via CWD) the runtime checkout.
- **DeploymentBinding owner:** same — a binding is keyed on `(repository_id, canonical_deployment_root)`; today the only `canonical_deployment_root` that matters for HBDC-REQ-042 is the runtime checkout's own root.

**Is conflating "PCAE runtime source checkout" with "the repository HBDC-REQ-042 verifies" intentional architecture, or a transitional limitation? — Intentional, as far as current contracts go, but narrower in scope than the governing prompt's framing assumed.** HBDC-001 v1.0 (§2, Scope) governs "deployment topology and environment configuration for a Class-B PCAE deployment under Model A" — i.e., PCAE's *own* deployment, not PCAE-managed third-party repositories. Nothing in HBDC-001, HMIC-001, or HATP-001 as currently frozen addresses a "managed application repository" identity/binding model at all. This is not a defect in 7F's evidence; it means **"managed repository onboarding architecture" is a separate, not-yet-started architecture question, entirely outside HBDC-REQ-042's current scope** — closing HBDC-REQ-042 does not require it and should not be blocked on it (Finding F2, §29, Non-Blocking).

## 19. DeploymentBinding vs. Certification — Ordering (resolved)

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §15:

> **HMIC-REQ-044.** `canonical_deployment_root` SHALL be derived exactly as `hatp_bootstrap.py::resolve_canonical_deployment_root`/`DeploymentBinding` already define it — the same Layer 2 binding that already defends against a copied `repository_instance_id` being reused at the wrong physical deployment.
>
> **HMIC-REQ-045.** Both identifiers SHALL be derived read-only by the admin tool at certify time... and re-derived read-only by the validator at validation time... never accepted as caller input on either path.

This settles the ordering question the governing prompt poses (§22): **Option A — a DeploymentBinding is created before certification, and certification's own `canonical_deployment_root` field is read (not independently computed or asserted) from the already-existing binding at certify time.** Certification does not create bindings (Option B, rejected by evidence) and binding creation is not deferred until after certification to "bind certified state to deployment" (Option C, rejected — the read direction in HMIC-REQ-044/045 runs from binding *into* the certification record, not the reverse).

## 20. DeploymentBinding vs. HMIC (source/certification identity)

Current `DeploymentBinding` schema (§8) does **not** contain `HMIC contract version`, `HMIC implementation digest`, `HMIC certification ID`, or a certification digest. It contains only `repository_id`, `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope`, `valid_from`, `status`, `revoked_at`. HMIC certification is a **separate record** (`CertificationRecord`, tracked elsewhere in the same trust store, keyed by `(repository_instance_id, canonical_deployment_root)` per the certification contract §15/§13) that references the same two identifiers but is not embedded inside, nor embeds, the `DeploymentBinding` record itself.

**This is a real architecture gap, not an oversight to paper over:** nothing in the current `DeploymentBinding` schema, or in any code that reads it, cross-validates that an active `DeploymentBinding` and an active `CertificationRecord` for the same `(repository_id, canonical_deployment_root)` key were issued by a consistent admin action, or prevents one existing without the other in an inconsistent state (e.g. a binding revoked but a certification left active, or vice versa) beyond both independently checking `status`. This is named as **Finding F3 (§29, Blocking for Boundary C, Non-Blocking for HBDC-REQ-042 alone)** — HBDC-REQ-042 itself only needs the binding, not the certification, to be `COMPLIANT`; but a future DeploymentBinding *producer* design (§26) must account for this cross-record consistency question, and a future contract-freeze phase should decide whether that consistency check is DeploymentBinding's responsibility, certification's, or a third coordinating record's.

## 21. DeploymentBinding vs. Protected Root

- `DeploymentBinding` records are stored **inside** the Protected Root's trust store, as entries in `registry.json`'s `deployment_bindings` array — not as a separate root, not referenced by pointer from elsewhere.
- The Protected Root itself does not "act as" deployment identity — it is the trust anchor / storage location, not a subject of identity.
- **One active binding per `repository_id`:** `_parse_registry_document` builds `deployment_bindings` as a `dict[str, DeploymentBinding]` keyed by `repository_id`, and explicitly raises on a duplicate key (`if record.repository_id in deployment_bindings: raise ...`, confirmed in source). **The schema mechanically enforces at most one binding entry per `repository_id` in the registry, active or not** — there is no "history of bindings for this repo" array; a re-bind would have to overwrite the single entry (mechanism for that: absent, §8).
- **Multiple repositories sharing one Protected Root:** yes, by construction — `deployment_bindings` is a dict of many entries, `principals`/`signers`/`authorities` likewise; the schema already supports multi-repository storage in a single trust store (§24 below expands on lookup/selection semantics).

## 22. DeploymentBinding vs. Host Identity

The Dell machine-id (`54ff22ce400b475aa0d55cb68f4a3334`) does **not** appear anywhere in the `DeploymentBinding` schema (§8), in `deployment_binding_matches()`'s comparison (which checks only `repository_id` and `canonical_deployment_root`), or in HMIC-REQ-044's derivation rule. **Current architecture binds repository + canonical path, not repository + host.** This is evidence-based, not a default assumption to fill a gap: host identity is deliberately absent from the current binding key, and this phase does not add it. The consequence (per HBDC-REQ-045, independently) is that host migration is handled by requiring a **new** binding entirely (`canonical_deployment_root` changes when the host changes, which forces a fresh `deployment_binding_matches()` failure until re-bound) — the architecture achieves host-migration invalidation *indirectly*, through path-comparison, not through an explicit host-identity field. Cloning/moving the trust store itself to a different host (a much stronger attack than moving the repository) is out of scope for `DeploymentBinding`'s own schema — it is mitigated by the trust store's own filesystem protections (HBDC-REQ-011..021: fixed platform path, admin-owned, never repository-local, never caller-overridable), which this phase does not reopen.

## 23. DeploymentBinding vs. Source SHA

**Not expected to survive normal PCAE source upgrades in the sense of "unaffected by them," but also not pinned to a specific commit SHA.** `DeploymentBinding`'s schema (§8) contains no `implementation_commit`, `source_sha`, or digest field at all — it binds `repository_id` (a stable UUID unaffected by commits, per §10) to `canonical_deployment_root` (a stable path unaffected by commits). A binding therefore **does not require rebinding on ordinary source updates** (new commits on the same checkout, same path) — nothing in `deployment_binding_matches()` compares source SHA. What *does* require fresh certification (a separate record, §20) on every source update is HMIC's own `implementation_scope_digest`/`implementation_commit` tracking — that is certification's job, not the binding's. **Binding tracks "this deployment instance," certification tracks "this source state was certified" — deliberately orthogonal, per the evidence, not a choice this phase invents.**

## 24. DeploymentBinding Lifecycle

**States, from the schema's own closed vocabulary** (`_STATUS_VALUES`, referenced by `_require_status`): the concrete values are not printed inline in the excerpted source above but the *consuming* logic (`deployment_binding_matches`) only ever branches on `binding.status != "active"` and `_require_revoked_at_consistency` only special-cases `"revoked"` vs. non-`"revoked"`. **Confirmed two-state closed vocabulary: `"active"` and `"revoked"`.** No `candidate`, `inactive`, `superseded`, or `expired` state exists in current schema or code.

- **Multiple bindings coexisting:** structurally, no — §21 confirmed the registry parser rejects a second entry for the same `repository_id` outright (raises on duplicate key). A repository can have **at most one** binding record at any time, whatever its status.
- **Active-binding selection semantics:** trivial by construction — `load_repository_enrollment(repository_id)` returns the single entry for that key (or `None`); `deployment_binding_matches()` additionally requires `status == "active"` and an exact `canonical_deployment_root` match. There is no "pick the most recent of several" selection logic anywhere, because the schema never allows several to exist simultaneously.

## 25. Binding Uniqueness

Given §21/§24: **exactly one binding entry may exist per `repository_id`** (schema-enforced, not merely a convention), and that entry is either `active` or `revoked` for the whole repository at once. There is no separate uniqueness constraint keyed on `(repository_id, canonical_deployment_root)` distinct from the `repository_id`-only key — meaning **a `repository_id`'s single binding entry names exactly one `canonical_deployment_root`**, so uniqueness-per-host and uniqueness-per-certification collapse into the same single-entry-per-`repository_id` fact. This closes the ambiguity the governing prompt's §28 raises: there is currently no schema shape that would allow "one binding per repository + Protected Root" to differ from "one binding per repository" — they are the same constraint today.

## 26. Binding Rotation and Revocation — Confirmed Gap

**No rotation mechanism exists.** If source/HMIC identity changes, certification changes, the repository path moves, the host changes, or key material rotates: current code has exactly one lever (`status`), and no function anywhere writes a new value into it, supersedes an entry, or replaces one binding with another. **No revocation mechanism exists either** — `status` supports the value `"revoked"` in the *read/validation* path (`_require_revoked_at_consistency` correctly parses and requires a `revoked_at` timestamp when status is `"revoked"`), meaning the schema is *ready* to represent a revoked binding, but **nothing in production code can ever transition a binding from `active` to `revoked`, or create one as `revoked` in the first place, because nothing can create or modify a binding at all** (§8). This is the same structural gap named there, restated in lifecycle terms: **read/validate is fully implemented for both binding states; write, for either state, does not exist.**

This phase does not design a fix for this gap in code — it names it precisely (Finding F4, §29, Blocking for any future DeploymentBinding producer design) so a future implementation phase does not repeat the CHGR-supersession limitation the governing prompt explicitly warns against (a lifecycle with no path to replace/revoke).

## 27. DeploymentBinding Authority — CHGR Condition 6 (verbatim)

Recovered directly from `.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json`, `conditions` field, condition 6, verbatim:

> "6) No venv reinstall, no wrapper mutation, no DeploymentBinding, no Boundary C, no Boundary A, no Cutover Record, no Permission Broker/POL-005/COMP-002 change, and no repository onboarding are authorized by this election, in this or any future phase, without a fresh, separate election."

This CHGR (`decision_subject`: Phase 149O.20L.7D.9's Dell redeployment + Action-9 PATH amendment proposition) governs a **narrower** decision than DeploymentBinding creation. Condition 6 is an explicit **exclusion list**, not a positive authorization for anything it names — it establishes that this particular election does **not** reach DeploymentBinding, Boundary C, Boundary A, Cutover Record, Permission Broker/POL-005/COMP-002, or repository onboarding, and that each requires **its own fresh, separate election** before being authorized in any future phase, this one included. **This phase does not satisfy that election — it explicitly does not attempt to (§74 of the governing prompt, honored).** Section 33 below addresses whether the same requirement extends to repository-identity creation.

Per §8's producer-absence finding, there is currently no code path a "fresh, separate election" for DeploymentBinding could even authorize the *execution* of — an election alone does not create the missing producer; a future implementation phase (§41) is a separate, additional prerequisite.

## 28. Repository-Identity Creation vs. the Election Requirement

Condition 6's exclusion list explicitly names "no DeploymentBinding" and "no repository onboarding," but **does not name repository-identity creation**. This is consistent with the broader evidence trail: HATP-REQ-048 states plainly that repository-identity creation "grants no HATP authority" and needs no human approval; the election requirement in CHGR condition 6 (and, more generally, in the CRI Model A architecture) attaches specifically to Layer 2 (binding/authority), not Layer 1 (identity). **Creating `.pcae/repository-identity.json` for the runtime checkout at `/opt/pcae/runtime/src` (e.g. via `pcae init` or a direct `ensure_repository_identity()` call) would not itself pre-decide, narrow, or partially satisfy any part of the DeploymentBinding election** — Layer 1 creation and Layer 2 authorization are architecturally and evidentially independent acts, and nothing found this phase suggests running `pcae init` against the runtime checkout would need its own fresh election under this or any current contract. **This phase does not perform that action** — it is a factual architecture conclusion, not an authorization; whether to actually run it is a decision for whichever phase is chartered to implement/execute against it (§40 below), which this phase is not.

## 29. HBDC-REQ-042 State Machine

| State | Repository identity | Active matching binding | Verifier reason | REQ-042 result |
|---|---|---|---|---|
| A | absent | n/a (never reached) | `no_repository_identity_present` | `False` — **current live Dell state** |
| A′ | present but malformed | n/a (never reached) | `repository_identity_malformed` | `False` |
| A″ | present (root unresolvable) | n/a | `canonical_deployment_root_unresolvable` | `False` |
| B | present, valid | trust store unreadable/malformed | `trust_store_unavailable` | `False` |
| C | present, valid | no binding, or binding present but wrong root/id, or `status != "active"` | `no_active_deployment_binding_matches_repository_and_root` | `False` |
| D | present, valid | present, `status == "active"`, `repository_id` and `canonical_deployment_root` both match | `deployment_binding_matches_repository_and_root` | `True` |

No additional intermediate states exist in current code — this table is exhaustive against §5's six terminal outcomes.

## 30. What COMPLIANT Would Mean

If state D (§29) is reached, `verify_class_b_deployment_conformance()`'s aggregate status may become `COMPLIANT` — but **only** if every other constituent check (topology, environment-lock, Model-A detection) also passes, per `ClassBConformanceStatus`'s HBDC-REQ-052/053 fail-closed, no-partial-credit rule. Preserving the required distinctions exactly:

- **HBDC COMPLIANT ≠ HMIC VALID.** They are separate verifiers over separate record types (`ClassBDeploymentVerificationResult` vs. `CertificationRecord`/validation), with no code path making one imply the other.
- **HBDC COMPLIANT ≠ Boundary C certified.** HBDC-REQ-049 is explicit: until a future HMIC v1.2 amendment binds HBDC-001 into `contract_versions` (HBDC-REQ-047/048, **not performed by any phase to date**), HBDC-001 conformance "does not mechanically gate `validate_active_hatp_mandatory_independent_verification_certification`'s result" — it is evidentiary/advisory only for certification purposes.
- **HBDC COMPLIANT ≠ HATP READY / activated.** However — and this is a real, current wiring fact, not hypothetical — as of Phase 149O.20L.3, HBDC conformance **is** mechanically wired as one additive term inside `assess_hatp_mandatory_activation_readiness` (HMRC-REQ-086-100, `hatp_mandatory_cutover.py`), where `class_b_deployment_conformance_satisfies_readiness` joins the existing conjunction of readiness checks for **Boundary A** (`HATP_MANDATORY` activation readiness) — never Boundary C. **Does current architecture use HBDC COMPLIANT as a prerequisite for Boundary C? — No, by HBDC-REQ-049's own explicit disclaimer, independently confirmed unmodified in current contract text.** **Does it use HBDC COMPLIANT as one (non-exclusive) prerequisite term for Boundary A activation readiness? — Yes, confirmed in current production wiring (§31).**

## 31. Boundary-C Entry Criteria (reconstructed) and a Stale-Docstring Finding

`hatp_class_b_conformance.py`'s own module docstring (dated to its 149O.20I authorship) states: *"none of the three 149O.20I modules is a member of HMIC-001's current 25-file frozen identity — `verify_class_b_deployment_conformance()`'s result MUST NOT be consumed by `hatp_mandatory_cutover.py` or any other authority-bearing production code path until a future, separately-governed phase evolves HMIC's source scope..."*

This is now **stale**, confirmed against current production source: `hatp_mandatory_certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES` constant, in a comment dated to Phase 149O.20K, explicitly states *"the final three entries, `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`, and `hatp_class_b_conformance.py`, were added at v1.3 by Phase 149O.20K's newly-added closure limb (c)"* — and lists all three inside the tuple. Independently, 7E's own evidence (`complete_28_file_hmic_byte_identity`) measured **28** canonical HMIC files, not 25, on live Dell — consistent with this expansion. And `hatp_mandatory_cutover.py` **does** already import and call `verify_class_b_deployment_conformance()` (§30 above) — exactly the consumption the docstring says "MUST NOT" happen.

**Finding F5 (§29 numbering continues below; Non-Blocking, documentation-only):** `hatp_class_b_conformance.py`'s module docstring was not updated when Phase 149O.20K brought it into HMIC's frozen scope and wired it into Boundary-A readiness. The current wiring is not itself a violation — 149O.20K is exactly the "future, separately-governed phase" the docstring calls for — but the docstring text is misleading to a future reader and should be corrected in a future documentation-touching phase. This phase does not edit `src/pcae/**` and therefore does not correct it here.

**Boundary-C entry criteria, reconstructed from primary evidence (not assumed to be REQ-042-only):** HMIC certification (`validate_active_hatp_mandatory_independent_verification_certification`) requires, per the certification contract: a resolved `repository_instance_id` and `canonical_deployment_root` (HMIC-REQ-043/044, both **read from the existing DeploymentBinding**, §19); `implementation_commit` (git HEAD SHA, HMIC-REQ-046); `implementation_scope_digest` over the frozen file set (HMIC-REQ-047+); a distinct HMIC contract-version binding (`contract_versions`); and — separately, per HBDC-001 §17 — HBDC-001 is *not yet* one of those bound contracts (HBDC-REQ-047), so Boundary C does not currently require HBDC COMPLIANT at all. **DeploymentBinding must already exist before certification can derive `canonical_deployment_root` from it (§19) — DeploymentBinding is therefore a prerequisite of Boundary C, but HBDC-REQ-042 COMPLIANCE (the full aggregator status) is not.**

## 32. Circular-Dependency Analysis

Tested explicitly for the cycle the governing prompt names: *"HBDC requires DeploymentBinding to become COMPLIANT; DeploymentBinding requires certification; certification requires HBDC COMPLIANT."*

- Edge 1 (HBDC-REQ-042 requires an active DeploymentBinding): **true**, confirmed §5/§29.
- Edge 2 (DeploymentBinding requires certification): **false** — nothing found anywhere requires an existing `CertificationRecord` before a `DeploymentBinding` can be created; `DeploymentBinding`'s write authority is purely admin-principal-based (HBDC-REQ-009), independent of certification status.
- Edge 3 (certification requires HBDC COMPLIANT): **false** — HBDC-REQ-049 explicitly disclaims mechanical gating of certification by HBDC conformance, confirmed unmodified in current contract text (§30/§31).

**No cycle exists.** Edge 2's absence alone breaks the loop — DeploymentBinding creation is causally upstream of both HBDC-REQ-042 compliance and (per §19) HMIC certification, and depends on neither. The dependency graph, as evidenced, is a DAG: `repository identity -> DeploymentBinding -> {HBDC-REQ-042 COMPLIANT, HMIC certification} -> Boundary-A readiness term (HBDC only) / Boundary C (certification only)`.

## 33. Bootstrap-Paradox Analysis

Tested: *does repository identity require onboarding, does onboarding require HBDC compliance, does HBDC compliance require repository identity?*

- Repository identity requires onboarding: **false** — repository identity is created against whatever tree `pcae init` is run in; for the tree that matters to the live Dell case (`/opt/pcae/runtime/src`, §17), that tree already exists and needs no onboarding at all (it *is* the runtime, not a to-be-onboarded managed repository).
- Onboarding requires HBDC compliance: no evidence found either way — no code path connects `/opt/pcae/projects/<repo-slug>/repo` provisioning to HBDC-REQ-042's status; this is simply an unconnected, not-yet-designed pair of concepts (§18), not a cyclic dependency.
- HBDC compliance requires repository identity: **true** (§5, step 2 gates everything after it).

**No paradox exists for the path this phase actually needs to reason about** (closing HBDC-REQ-042 for the runtime checkout). The three-way cycle the prompt asks about does not materialize because "onboarding" and "HBDC compliance" are not currently connected by any dependency edge at all in either direction — they are simply orthogonal today (§18's conclusion, restated in paradox-testing terms).

## 34. Minimal Valid Future Sequence (derived, not assumed)

Derived strictly from §5 (verifier order), §7 (identity producer exists), §8 (binding producer absent), §19 (binding-before-certification ordering), §27-28 (election scope), and §32 (no cycle):

1. **Repository identity creation** for the runtime checkout (`/opt/pcae/runtime/src`) — mechanism already exists and requires no election (§7, §28). Not authorized by this phase to execute; named as the first step a future phase could take.
2. **DeploymentBinding producer design and implementation** — does not exist yet (§8); a future, separately-governed **implementation** phase (not this one) must design and build a governed, schema-validated, admin-authorized creation path (§41 sketches its conceptual shape; no code is written this phase).
3. **A fresh, separate human election** authorizing that specific DeploymentBinding proposition (§27) — required before step 4 executes, per CHGR condition 6's pattern and per HBDC-REQ-009's admin-exclusivity.
4. **DeploymentBinding creation** (admin-executed, out of PCAE-agent reach per the trust model) — the actual write.
5. **HBDC-REQ-042 re-verification** — Action 9 re-run; expected `deployment_binding_matches_repository_and_root`, contributing toward (not alone sufficient for) overall `COMPLIANT`.
6. **HMIC certification proposition and certify-time derivation** (reads the now-existing binding, §19) — a distinct, separately-governed step; not authorized or begun by this phase.
7. **Certification** (Boundary C) — requires its own governed phase and independent verification; not gated by step 5's HBDC result today (§31), though a future HMIC v1.2 amendment (HBDC-REQ-048) could change that.
8. **Boundary-A activation readiness re-assessment** — HBDC-REQ-042's contribution to `assess_hatp_mandatory_activation_readiness` (§30/§31) becomes satisfied; other readiness terms are unaffected by this phase and remain to be independently assessed at that time.

**This is the real derived sequence — it is not identical to the governing prompt's own illustrative example**, most notably in that repository-identity creation (step 1) does not require an election (§28) and is causally and authority-wise disconnected from the binding election (steps 2-4), and in that certification (steps 6-7) is not gated by HBDC's own COMPLIANT result under current contracts (§31). No step in this sequence is executed by this phase.

## 35. Placeholder Deployment Identity — Rejected

The governing prompt asks whether an infrastructure deployment can be bound before an actual managed project is onboarded, and whether a placeholder identity is warranted. Per §16-18: **no placeholder identity is needed or invented.** The runtime checkout at `/opt/pcae/runtime/src` is not a placeholder — it is the actual, real repository (`pcae-harness` itself, HEAD `28bf137b...`) that HBDC-REQ-042 currently evaluates. Repository onboarding (managed-project repositories) remains a distinct, unconnected, not-yet-designed future architecture area (§18) — this phase does not invent a placeholder concept to bridge it, per the prompt's own explicit instruction not to.

## 36. Producer Architecture (conceptual only — DeploymentBinding)

No implementation. Conceptual responsibilities for a future implementation phase to design in full:

- **Caller:** admin OS principal only, operating out-of-band from any PCAE-agent-invoked code path (mirrors HBDC-REQ-009/012's existing Protected-Root-creation discipline — never agent-invocable, even indirectly).
- **Inputs:** `repository_id` (read from the target repository's existing `RepositoryIdentity`, never caller-typed free text — mirrors HMIC-REQ-045's read-only-derivation discipline); `canonical_deployment_root` (derived via `resolve_canonical_deployment_root`, never accepted as a raw path string); `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` (from the admin's own enrollment context, not from repository-local state).
- **Output:** one new `DeploymentBinding` entry, `status="active"`, `valid_from` set to creation time.
- **Validation:** re-use `_parse_deployment_binding`'s existing closed-schema checks; reject if an entry for this `repository_id` already exists (§21/§24 — the schema already forbids duplicates; a producer must fail closed here rather than silently overwrite).
- **Persistence:** atomic write into `registry.json`, following the same temp-file/fsync/rename discipline `repository_identity.py::_write_atomic` already establishes elsewhere in this codebase — no new idiom needed.
- **Failure behavior:** fail closed on any malformed input, pre-existing entry, unreadable/malformed registry, or non-admin caller context; never partially write.
- **Idempotency:** creating a binding for a `repository_id` that already has an active, identical binding should be a safe no-op; creating one where an existing (different) entry is present must fail, not silently overwrite (rotation/revocation, §26, is a *distinct*, separately-designed operation, not folded into "create").
- **Audit evidence:** should participate in this repository's existing governance-record/provenance-record infrastructure (the same machinery CHGR records, publication-execution records, etc. already use) rather than inventing a bespoke audit trail.

## 37. Producer Architecture (conceptual only — Repository Identity)

Already substantially implemented (§7); the remaining conceptual gaps for a future phase, if ever prioritized:

- **Rotate:** not designed. Would need to define whether rotation invalidates the existing binding automatically (likely yes, per §10's "mutation fails closed" security posture) or requires the admin to separately revoke first.
- **Revoke/delete:** not designed — same fail-closed consequence as mutation (§10's attack matrix already covers deletion: HATP-01 architecture treats it as "fails closed, HATP unavailable," which needs no new mechanism, only documentation, since the *existing* fail-closed behavior already handles it correctly by absence).
- **Repair:** deliberately **not** provided — `RepositoryIdentityMalformedError` is raised and left for a human/operator to resolve; auto-repair was explicitly rejected as a design principle (module docstring: "never silently regenerated").
- **Import/migrate:** not designed; 149O.1B.2 §17 names an eventual `pcae repository reidentify`-equivalent as conceptually the right shape, "deliberately sensitive... not implemented, not named as a frozen command surface" — this phase does not change that disposition.

## 38. CLI/API Architecture (conceptual only)

Consistent with existing CLI conventions (subcommand families like `pcae session bootstrap`, `pcae task ...`), a future implementation phase would plausibly introduce:

- `pcae repository identity {inspect|create}` — `inspect` wraps `read_repository_identity`; `create` wraps `ensure_repository_identity` (largely redundant with `pcae init`'s existing side effect, so this may not warrant a dedicated command at all — an open question for that future phase, not decided here).
- `pcae deployment binding {inspect|create|revoke|list}` — `inspect`/`list` read-only, wrapping `HATPTrustStore` lookups; `create`/`revoke` admin-principal-only, wrapping the producer design in §36.

**No name is committed to** — this phase explicitly avoids freezing CLI surface, per its own charter. The capability list (inspect, create, verify, activate, revoke, list) mirrors the governing prompt's own enumeration; "activate" is intentionally not attached to DeploymentBinding here — activation is Boundary-A/Cutover-Record's concept, not DeploymentBinding's, per the distinctions preserved in §2 of the governing prompt and reconfirmed throughout this document.

## 39. Fail-Closed, Atomicity, and Ownership Principles (conceptual only)

For any future producer (repository identity's existing implementation already satisfies these; DeploymentBinding's future implementation should mirror them exactly):

- **Fail-closed cases to define:** malformed identity input, duplicate `repository_id` binding, mismatched repository root, mismatched Protected Root, mismatched HMIC identity (§20's cross-record consistency gap), multiple simultaneous active bindings (already schema-prevented, §21/§24), unknown schema version, ambiguous target repository, partial write, integrity mismatch. Each should raise a specific, named exception (mirroring `RepositoryIdentityMalformedError`/`HATPTrustStoreMalformedError`'s existing pattern) — never a silent no-op, never a best-effort partial result.
- **Atomicity:** temp file in the same directory as the target, `fsync` before rename, `os.replace` for the atomic swap, directory-fsync where the target filesystem requires it, symlink-rejection both before and after the write race window — this repository already has two working reference implementations (`repository_identity.py::_write_atomic`, and the pattern cited there from `cltr/persistence.py`/`governance/publication/storage.py`) that a DeploymentBinding producer should reuse, not reinvent.
- **File ownership/modes:** DeploymentBinding lives under Protected Root, which is already root-owned/`0750`-class per HBDC-REQ-013/014; **the guiding principle, not a specific mode this phase asserts as new**, is: the agent principal must never be able to forge or alter an authority-bearing binding, directly or via any parent-path/symlink/ACL channel (HBDC-REQ-015..021, already frozen and unmodified).

## 40. Anti-Spoofing Analysis

| Attack | Evidence that prevents it |
|---|---|
| Copy another repository's identity into a different repo | Layer 2 lookup keys on `repository_id`; the copied ID's binding (if any) names the *original* repo's `canonical_deployment_root`, which the copy's own resolved root will not match (`deployment_binding_matches`) |
| Copy trust-store binding to another host/root | Not reachable by an agent at all — Protected Root is admin-owned, agent-unwritable (HBDC-REQ-007/013-021); even if it were copied, `canonical_deployment_root` comparison fails on the new host's differing path (§18, §22) |
| Change repository root path | `resolve_canonical_deployment_root` recomputes on every check; a changed path no longer matches the bound value, so `deployment_binding_matches` returns `False` until admin re-bind (HATP-REQ-055/056) |
| Clone identity into two concurrent deployments | Both share the same `repository_id`, but only one `canonical_deployment_root` can match the single binding entry (§21/§25 — the schema forbids two entries for one `repository_id`), so at most one of the two clones can ever match |
| Bind wrong HMIC identity | Out of `DeploymentBinding`'s own schema scope (§20) — this is the one gap this phase names as unresolved, not a defended attack |

## 41. Multi-Deployment and Multi-Repository Semantics

- **One repository, deployed to Dell + another host + future CI:** each independent on-disk instance gets its **own** `repository_instance_id` (fresh `pcae init` per instance, no cross-instance sharing by convention, §14) and, if authorized, its own independent `DeploymentBinding`. This is explicit, evidenced architecture (149O.1B.2 §11's clone/worktree rows), not an inference.
- **Multiple governed repositories on one shared host/trust store:** the schema already supports it mechanically (§21 — `deployment_bindings` is a dict keyed by `repository_id`, not a single-slot field). Lookup/selection is trivial and already implemented: `load_repository_enrollment(repository_id)` is a pure key lookup; no centralized cross-repository governance logic exists or is implied by shared storage — each repository's binding is independently keyed and independently matched. **Shared storage does not imply shared or centralized governance** — each `(repository_id, canonical_deployment_root)` pair is evaluated independently.
- **Repository slug (`/opt/pcae/projects/<repo-slug>/repo`):** confirmed **not** used as authority identity anywhere in `repository_identity.py`, `hatp_bootstrap.py`, or the verifier chain. `slug != repository identity` — the slug, where it exists at all, is purely filesystem organization for a not-yet-designed managed-repository-onboarding scheme (§18), entirely disconnected from `repository_instance_id`/`DeploymentBinding`.

## 42. Current PCAE Harness Deployment's Own Identity

Should the Dell runtime's own checkout (`/opt/pcae/runtime/src`) have a repository identity? **Yes, evidenced, not accidental:** it is exactly the tree Model A already requires PCAE's own authority modules to execute from (§17), and it is the tree HBDC-REQ-042's live verifier already evaluates. Creating an identity for it is not "accidentally onboarding pcae-harness as a managed project" — pcae-harness's runtime checkout was never a candidate for the *managed-project* concept in the first place (§18); it is PCAE's own deployment, which HBDC-001 has governed since v1.0 regardless of any future managed-repository work. No mismatch exists here once §17-18's distinction is made explicit — the mismatch the governing prompt worried about (§55-56 of the prompt) would only materialize if a future phase conflates *managed-repository* onboarding architecture with *this* runtime-deployment identity/binding work; this document's terminology (§3) exists specifically to prevent that conflation going forward.

## 43. HBDC Subject, DeploymentBinding Subject, Certification Subject — Alignment Check

- **HBDC subject:** a `(repository deployment instance, canonical root)` pair — confirmed by `_check_deployment_identity`'s own two inputs (§5).
- **DeploymentBinding subject:** the identical pair, `(repository_id, canonical_deployment_root)` — confirmed by its schema (§8) and its match function (§5 step 4).
- **Certification subject:** the identical pair again, per HMIC-REQ-043/044 (§19) — explicitly derived "exactly as" the same two functions define them, not independently computed.

**All three subjects are aligned on the same `(repository_id, canonical_deployment_root)` pair.** No divergence found — this is a clean result, not a finding requiring remediation.

## 44. Findings Summary

| ID | Finding | Blocking? |
|---|---|---|
| F1 | HBDC-REQ-042's contract text ("identity alone confers no authority") and the production verifier's stronger positive check (identity present AND matching active binding) are related but not 1:1 textual — implicit mapping (§4) | Non-Blocking (identity creation, binding creation) |
| F2 | No architecture connects HBDC-REQ-042 to a "managed application repository" concept; only the runtime's own checkout is currently in scope (§17-18) | Non-Blocking (for closing REQ-042); Blocking (for any future multi-repo-deployment work until designed) |
| F3 | `DeploymentBinding` schema has no cross-validation against HMIC `CertificationRecord` state for the same `(repository_id, canonical_deployment_root)` key (§20) | Non-Blocking for HBDC-REQ-042 alone; Blocking for Boundary C readiness design |
| F4 | No rotation or revocation write-path exists for `DeploymentBinding`, though the schema already supports representing a revoked state (§26) | Blocking for any future DeploymentBinding producer design (must not repeat the CHGR-supersession gap) |
| F5 | `hatp_class_b_conformance.py`'s module docstring is stale relative to Phase 149O.20K's actual wiring into `hatp_mandatory_cutover.py`/HMIC's 28-file frozen scope (§31) | Non-Blocking (documentation only) |
| F6 | No `DeploymentBinding` producer/creation mechanism exists anywhere in production — read/match only (§8, independently reconfirms 7E) | Blocking for DeploymentBinding creation |
| F7 | No repository-identity rotate/revoke/repair/import/migrate mechanism exists (create/read only) (§37) | Non-Blocking (not required to close HBDC-REQ-042; a future-work note) |

No finding is manufactured where evidence was clean — §43's subject-alignment check and §32/§33's cycle/paradox analyses both returned clean (no finding), and are reported as such rather than omitted.

## 45. Current REQ-042 Status (unchanged by this phase)

**OPEN — SOLE HBDC RESIDUAL.** Live reason, as measured by 149O.20L.7E and not re-measured this phase (§2): `no_repository_identity_present`. Downstream binding absence (`no_active_deployment_binding_matches_repository_and_root`) remains unresolved and unmeasured on this specific run, because evaluation order (§5) never reached it. This phase does not claim REQ-042 is repaired, closer to repaired in code, or newly measured — only that its architecture is now fully reconstructed from primary sources.

## 46. Expected Clean Outcome (confirmed, this phase's exit state)

```
Dell Boundary P                 INDEPENDENTLY VERIFIED PROVISIONED (149O.20L.7E, unchanged)
HBDC                            NON_COMPLIANT — SOLE RESIDUAL HBDC-REQ-042
Repository identity architecture   DEFINED (this phase)
DeploymentBinding architecture     DEFINED (this phase)
Repository identity artifact       NOT CREATED
DeploymentBinding                  NOT CREATED
HMIC                            DEPLOYED SOURCE IDENTITY NOT CERTIFIED FOR BOUNDARY C
Boundary C                      NOT AUTHORIZED
Boundary A                      NOT AUTHORIZED
HATP                            NOT READY
Runtime                         Observed / observe / unavailable (unchanged)
```

## 47. Proof of No Dell Mutation, No Onboarding, No Implementation

- No SSH session to any Dell host was opened this phase (§2).
- No `.pcae/repository-identity.json` was created (checked: still absent in this repository's own working tree, §15; never touched on Dell — no Dell access occurred at all).
- No `DeploymentBinding` was created (no trust-store write path exists to have used, §8).
- No repository was onboarded; `/opt/pcae/projects` was not touched (no Dell access occurred).
- `git diff --name-only <phase-entry>..HEAD -- src/pcae/` — this phase's own commits touch none of `src/pcae/**` (verified at commit time, §49).
- `git diff --name-only <phase-entry>..HEAD -- docs/contracts/` — no contract file modified.
- No CLI command was implemented. No schema was changed. No Permission Broker, POL-005, or COMP-002 change was made. No HMIC certification was computed, requested, or granted. No Cutover Record was created. No Boundary C or Boundary A action was taken.

## 48. Governance Results (this phase)

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated — same historical `tasks/done/`/`tasks/DONE.md` entries 7E already carried forward, not remediated here, outside this phase's allowed-file scope)
- **pcae_push_check:** clean (nothing_to_push, at phase entry)
- **pcae_runtime_inspect:** Observed / observe / unavailable (unchanged)
- **pcae_notify_status:** telegram configured/enabled
- **pcae_phase_report_reconcile (149O.20L.7E):** reconciled, mutation none

## 49. Runtime State

`pcae runtime inspect`, run this phase (§2): Observed / observe / unavailable — unchanged by this architecture-only phase, as expected (§76 of the governing prompt).

## 50. Recommended Next Phase

Per §31/§36's evidence — repository-identity architecture is fully defined **and already implemented/production-tested** (Outcome A does not apply cleanly: it is not "mostly specified," it is *fully* specified and built); DeploymentBinding architecture is now fully defined but **entirely unimplemented** (Outcome C, precisely):

**149O.20L.7G — DeploymentBinding Producer Contract/Schema Evolution and Implementation Planning.** Scope: (a) extend HBDC-001 or a new bound contract with explicit normative requirements for DeploymentBinding creation (producer responsibilities per §36: caller, inputs, validation, atomicity, fail-closed rules, audit evidence — contract text, not code); (b) resolve Finding F3 (§44) — decide, normatively, how DeploymentBinding and CertificationRecord cross-consistency is guaranteed or explicitly accepted as independently managed; (c) resolve Finding F4 (§44) — define rotation/revocation lifecycle normatively before any implementation phase builds a producer that would otherwise repeat the CHGR-supersession gap. This is a contract/schema-evolution and implementation-planning phase, not an implementation phase — actual DeploymentBinding creation code, and the fresh election required to authorize its first real use (§27), remain separately gated, later steps (§34, steps 2-4).

This phase does not initiate that election, does not draft that contract text, and stops here, as instructed.
