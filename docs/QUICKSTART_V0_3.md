# PCAE v0.3 Quickstart — Your First Governed Proposal in ~5 Minutes

This is the fast path: install PCAE, govern a task, and watch it accept
an in-scope proposal and reject an out-of-scope one — with an audit
trail for both. It optimizes for **time-to-first-governed-proposal**,
not full architecture understanding (for that, see
[docs/ARCHITECTURE.md](ARCHITECTURE.md)).

Every command below was mechanically executed against a fresh disposable
repository — the original walkthrough as part of Phase
149O.20L.7O.2U.4's acceptance evidence
(`docs/PHASE_149O_20L_7O_2U_4_DENY_ALLOW_DEMO_AND_QUICK_START_DOCUMENTATION.md`),
and the `pcae intake from-files` golden path below as part of Phase
149O.20L.7O.2Z's installed-wheel/sdist clean-environment smoke tests.
This is not aspirational documentation.

---

## 1. What PCAE Does

PCAE is a lightweight governance layer you run *alongside* an existing
AI coding agent (Claude Code, Cursor, or any tool that can describe the
files it changed). It does not run or replace your agent. It:

- **Gates task scope** — a governed task declares which paths an agent
  may touch; proposals outside that scope are rejected before anything
  reaches your repository.
- **Validates proposals against real repository state** — every
  proposal is checked against the actual repo (fingerprint, base
  commit, per-file content hash), not trusted on the producer's word.
- **Produces an audit trail** — every accepted or rejected proposal is
  a stored, inspectable record, and every promotion into your
  repository requires an explicit human review step.

PCAE does **not** autonomously execute your coding agent. Runtime
execution capability remains `Observed` / `observe` / `unavailable` in
this release — see [§13](#13-what-pcae-does-not-yet-do).

## 2. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.9 | `python3 --version` |
| Git | any modern version | required for hooks and repo binding |
| pip | ≥ 21 | included with Python ≥ 3.9 |

No account, no credential, no network service, no domain/DNS/TLS, and
no hardware key (FIDO2/WebAuthn) are required for this quickstart.

## 3. Install / Enter Repository

PCAE v0.3 is **not yet published to PyPI** (true of v0.1 and v0.2 as
well — GitHub release assets only). Install from source:

```bash
git clone <this-repository-url>
cd pcae-harness
pip install -e .
```

Then, in the **separate** repository you want to govern:

```bash
cd /path/to/your/project
```

## 4. Initialize PCAE

```bash
pcae init
```

This scaffolds `.pcae/`, task/session files, and Git hooks in your
repository. Each repository has independent PCAE state.

## 5. Create a Governed Task/Scope

```bash
pcae task new "Update greeting message in app.py" \
  --goal "Change the greet() function's message text" \
  --allowed-file "src/app.py" \
  --mode implementation
```

`--allowed-file` (repeatable) is the scope boundary every proposal will
be checked against. Confirm it:

```bash
pcae task show
```

## 6. Prepare an Agent Proposal

An external agent proposes changes as a small JSON document (the
**generic intake contract**, frozen in Phase 149O.20L.7O.2U.1) — a
diff-like description with per-file content and a content hash, bound
to a specific repository fingerprint and base commit.

You do not need to hand-build this JSON yourself. The reference adapter
does it for you — see the next step.

## 7. Submit a Proposal With `pcae intake from-files`

PCAE core is producer-agnostic. `pcae intake from-files` is the
packaged, generic CLI command every producer uses to build and submit
an Intake Candidate directly from local file changes — no tool-specific
adapter script required, for Claude Code or any other tool:

```bash
pcae session bootstrap --agent-id claude-local   # or codex-ox, or any custom identity
pcae intake from-files \
  --task-id <task-id-from-step-5> \
  --candidate-id allow-1-greeting-update \
  --file "src/app.py:modify:/path/to/new_content.txt" \
  --summary "Update greet() to say 'Hello there' instead of 'Hello'" \
  --self-reported-complete
```

It computes the repository fingerprint and base commit itself from real
Git state — it never trusts a caller to supply them, since those are
exactly the fields PCAE uses to reject a stale or foreign proposal. It
cannot set `promotion_authorized`, `execution_allowed`, or any other
authority-bearing field; those do not exist in its input or output at
all. Under the hood it builds the same generic intake contract shown in
the [Appendix](#appendix-generic-producer-not-claude-code) and submits
it exactly as `pcae intake create --candidate-file <path> --json` would.

Producer identity (`claude-local`, `codex-ox`, or any string) is derived
from the active PCAE governance agent lock (`pcae session bootstrap
--agent-id <id>`) when one is held, or accepted explicitly via
`--producer` otherwise. Either way it is recorded as descriptive
provenance only — it never affects acceptance, promotion, or authority.
Claude Code is the first reference producer, not a requirement — see
[§9](#9-generic-producer-a-tool-that-isnt-claude-code).

> **Legacy path:** `scripts/claude_code_intake_adapter.py` is a
> repository-only reference script (not part of the installed package)
> that predates `pcae intake from-files` and is now a thin, deprecated
> wrapper over it:
> ```bash
> python3 /path/to/pcae-harness/scripts/claude_code_intake_adapter.py \
>   --task-id <task-id-from-step-5> \
>   --candidate-id allow-1-greeting-update \
>   --file "src/app.py:modify:/path/to/new_content.txt" \
>   --summary "Update greet() to say 'Hello there' instead of 'Hello'" \
>   --self-reported-complete
> ```
> Kept as a reference example only; `pcae intake from-files` is the
> supported, packaged, installed-CLI path above.

## 8. Inspect It

```bash
pcae intake show --intake-id <intake-id-from-output>
```

Shows validation outcome, integrity status, and the resulting ECP
(ExecutionChangePackage) ID — with `execution_allowed: False` and
`promotion_executed: False` on every intake record, always.

## 9. See an In-Scope Proposal Accepted

An in-scope, hash-valid, repo/base-bound proposal is `accepted`:
`validation_outcome: accepted`, an `ecp_id` is populated, and it is
discoverable via:

```bash
pcae intake list
```

Acceptance means "this is verified, non-authorizing evidence" — **not**
"this is now applied to your repository." That distinction is load-
bearing; see [§10](#10-see-an-out-of-scope-proposal-denied).

## 10. See an Out-of-Scope Proposal Denied

Run the same path with a file **outside** the task's `--allowed-file`
scope (e.g. `README.md` when only `src/app.py` is in scope):

```bash
pcae intake from-files \
  --task-id <task-id-from-step-5> \
  --candidate-id deny-1-readme-edit \
  --file "README.md:modify:/path/to/other_content.txt" \
  --summary "Add copy to README" \
  --self-reported-complete
```

Result: `accepted: false`, `rejection_reasons: ["out_of_scope_path:README.md"]`,
`ecp_id: null` — a structurally, hash-, and repo-valid proposal, rejected
specifically by task-scope governance. No ECP, no promotion path, and no
change to `README.md` on disk. The rejection itself is still a stored,
auditable record (`pcae intake show`/`list` surface it).

## 11. Continue Into Governed Review / Promotion

An accepted intake is an ordinary ECP — it goes through PCAE's existing,
unmodified human-review and promotion chain, unchanged by this release:

```bash
pcae promotion-review create \
  --ecp-id <ecp-id-from-step-9> \
  --reviewed-by <your-name> \
  --disposition approved \
  --approved-path src/app.py \
  --promotion-authorized \
  --review-rationale "Small in-scope change reviewed and approved."

pcae promote --epr-id <epr-id-from-output> --dry-run   # preview first
pcae promote --epr-id <epr-id-from-output>              # writes the file
```

`pcae promote` is the **only** command in this chain that writes to your
repository's working tree, and only for paths an EPR explicitly
approved. It never runs `git add`/`commit`/`push` on your behalf.

## 12. Understand the Audit Trail

For any proposal you can always answer, from stored records alone: what
was proposed, against which repository/base commit/task, whether it was
in scope, whether its content hash verified, whether it was accepted,
who reviewed it and with what disposition, and whether/how it was
promoted. Use `pcae intake show`, `pcae intake list`,
`pcae execution-change-package show`, and `pcae promotion-review show`
to inspect any stage.

## 13. What PCAE Does NOT Yet Do

- **No autonomous execution.** PCAE does not run your coding agent for
  you. Runtime posture remains `Observed` / `observe` /
  `execution_unavailable` — unchanged by this release.
- **No enterprise identity/deployment features required or used here** —
  no HATP, no FIDO2/WebAuthn, no domain/DNS/TLS. Those are separate,
  deferred enterprise-extension work, not part of this workflow.
- **No PyPI package yet** — install from source (§3).
- **Claude Code is one reference producer, not a requirement** — any
  tool that can emit the generic intake JSON contract can participate;
  see the generic example below.
- **Platform scope:** this quickstart and its command sequence were
  exercised on macOS/Linux. Windows support for the intake path has a
  documented, carried-forward Non-Blocking gap (an absolute-path check
  that only reliably detects POSIX-style paths); Windows is not claimed
  here.
- **Repository fingerprint is content-bound, not location-bound.**
  `repo_fingerprint` is a hash of the repository's root commit(s), by
  design stable across clones and forks of the same history. Two
  independently created repositories that happen to share
  byte-identical genesis commit(s) would share the same fingerprint —
  this is not a way to impersonate an unrelated real repository, but it
  is not a location-unique identifier either.

## Appendix: Generic Producer (Not Claude Code)

PCAE's intake contract is generic JSON — any tool can produce it. This
is the same document shape the Claude adapter builds automatically,
shown directly so you can see the contract does not depend on Claude
Code in any way:

```json
{
  "intake_contract_version": "1.0",
  "candidate_id": "any-stable-id",
  "producer": {"kind": "your-tool-name", "adapter_version": "1.0"},
  "task_context": {"task_id": "<task-id>", "declared_goal": "..."},
  "repo_binding": {
    "repo_fingerprint": "<sha256 of root commit(s), see repo_fingerprint below>",
    "base_commit": "<current HEAD sha>"
  },
  "proposed_changes": [
    {
      "path": "src/app.py",
      "operation": "modify",
      "content_after": "<full new file content>",
      "content_hash_after": "<sha256 of content_after>"
    }
  ],
  "producer_claims": {"summary": "...", "self_reported_complete": true}
}
```

Submit it the same way: `pcae intake create --candidate-file <path>
--json`. No second real adapter is required to exercise this — the
point is that the contract, not Claude Code, is what PCAE governs.
