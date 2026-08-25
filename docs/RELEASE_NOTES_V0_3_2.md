# PCAE v0.3.2 Release Notes (Release Candidate)

## Overview

PCAE v0.3.2 surfaces mature capabilities that were already present in
the installed product: Repository Intelligence, runtime/plugin
introspection, the interactive governance workflow (`decision-session`
+ `governance-record`, producing Canonical Human Governance Records —
CHGRs), and authority-state inspection. These capabilities pre-existed
in PCAE (some since `v0.2.0`) and are now promoted to documented
supported workflows after independent verification from a freshly
built, clean-installed wheel and sdist (Phases 149O.20L.7O.3A–3C).

This is an **exposure/productization release**, not a new-feature
release. **Zero production source, CLI, contract, or schema changes**
were made in Phase 3B or 3C; the only source change in this release is
version metadata (`pyproject.toml`, `src/pcae/__init__.py`:
`0.3.1` → `0.3.2`).

## Newly Documented Capabilities

### Repository Intelligence

```
pcae repository-intelligence snapshot generate [--output <dir>] [--pretty] [--json]
pcae repository-intelligence query --snapshot <path> (--entity <id> | --capability <id> | --contract <id> | --attribution <target> | --limitations | --boundary) [--json]
pcae repository-intelligence change-impact --snapshot <path> --change <text> --entity <id> [--output <path>] [--json]
pcae advisory context build --snapshot <path> (--entity <id> | --capability <id> | --contract <id>) [--purpose <text>] [--output <path>] [--json]
```

- **`snapshot generate`** is a **LOCAL DERIVED-ARTIFACT GENERATION**
  workflow — it deterministically writes `.pcae/repository-intelligence/
  latest.json` and a timestamped copy under
  `.pcae/repository-intelligence/snapshots/` in the *current working
  directory's* repository. It performs no network access, invokes no
  model, executes no arbitrary code, and never mutates project source
  files or git history — but it does write local derived PCAE state,
  and is documented as such, not as "read-only."
- **`query`, `change-impact`, and `advisory context build`** are
  READ-ONLY: they operate over an already-generated snapshot file
  passed via `--snapshot` and write nothing (`--output`, where
  supported, writes only an explicitly requested report file, never
  `.pcae/` state).
- **Scope, confirmed unchanged from Phase 3A/3B and independently
  reproduced in 3C:** `snapshot generate` requires the target working
  tree to contain `src/pcae/`, `tests/`, and
  `schemas/repository_intelligence/` at its top level — hardcoded
  paths in `src/pcae/repository_intelligence/snapshot_builder.py`.
  Against a bare disposable repository it fails closed; against a
  `pcae-harness`-shaped checkout it succeeds. This is **self-inspection
  tooling for PCAE contributors**, not a general "analyze any
  repository" product feature, and is documented that way — not
  advertised as a general-audience README headline.

### Runtime / plugin introspection

```
pcae runtime inspect [--json]
```

Zero prerequisites, zero side effects (verified from a bare disposable
`git init` repository with no prior PCAE state; `git status` unchanged
before and after). No backend invocation, no subprocess execution
beyond the CLI process itself, no network activity, no authority
mutation. Reports the current runtime posture honestly: no plugin
loader exists yet, so `Plugin count: 0` / `Registry status: empty` is
correct, expected output, not an error state. This is a full,
general-purpose product workflow — works identically in any
repository.

### Interactive Workflow / CHGR

```
pcae decision-session create/evidence/select/preview/confirm/readiness
pcae governance-record publish/inspect/verify
```

Full end-to-end sequence independently re-exercised in a disposable
repository during this phase and confirmed to complete correctly,
producing a real, schema-conformant CHGR (Canonical Human Governance
Record) on disk under `.pcae/publication-execution/records/`.
Boundaries preserved and documented explicitly:

```
preview != confirmation
confirmation != authorization
readiness != publication
publication != arbitrary execution
CHGR != runtime execution authority
```

`preview` reads current session state and changes nothing. `confirm`
requires echoing back the exact `preview_digest` from `preview` — the
binding mechanism. `readiness` performs a local write (a pending
package) on first call. `governance-record publish` is the
human-authorizing act that writes the CHGR; it authorizes nothing
outside the governance-record system itself. `governance-record
inspect`/`verify` are read-only.

A CHGR's own inspect/verify output states explicitly that successful
validation "does not establish that the represented governance act was
valid, applicable, current, or performed by an authorized human." CHGR
is a schema-conformant governance record, not an execution grant.

**Known, non-blocking rough edge (documented, not repaired):** a
`governance-record publish` call with a schema-nonconformant field
(e.g. a `--template-version` not matching `^[0-9]+\.[0-9]+$`, or fewer
than two `--options-presented` values) is reported as a generic
`internal_error` rather than a specific `invalid_request`-shaped
message, because `run_with_error_mapping` in `decision_session.py`
maps every non-`ApplicationServiceError`/`ValueError` exception —
including the legitimate `ChgrSchemaConformanceError` this raises — to
the same opaque message. The workflow itself completes correctly with
conformant input (independently reproduced in this phase). This is a
UX polish item, not a defect blocking release.

### Authority inspect

```
pcae authority inspect <path> [--json]
```

Inspects one explicit Typed Authority Model (TAMPC-001 v1.0) record
artifact file. Requires an explicit path — there is no no-argument
"current state" mode. Independently reverified: it does not create,
activate, transfer, or mutate authority; does not change epochs or
pointers; does not perform cutover or recovery; leaves the target
repository's `git status` unchanged. **Inspection is not activation.**

`pcae cltr migration status` continues to report `production_authority:
"legacy"` and `authority_cutover: false` — current production
authority remains legacy, stated in that terminology; this release
does not imply or perform any CLTR cutover. No production-generated
example artifact of a CLTR-family record exists in this repository
today, so this capability is documented narrowly, as advanced
CLTR-migration tooling — not a README headline feature.

## Runtime Boundary (Unchanged)

```
Runtime state: Observed
Maximum capability: observe
Execution availability: unavailable
```

v0.3.2 does **not** activate autonomous execution, a plugin loader, or
any new authority. None of the four newly documented capabilities
change this posture.

## Unchanged Capabilities

The `v0.3.0`/`v0.3.1` intake golden path (`pcae init` → `pcae session
bootstrap` → `pcae task new` → `pcae intake from-files` → `pcae intake
show/list`), Codex-Ox agent registration, and the no-lock/explicit-
`--producer` compatibility path are all unchanged and re-verified in
this phase. This release does not re-advertise them as new — they
pre-existed and are simply confirmed unaffected.

## Package Boundary

All four newly documented capabilities are packaged in both the wheel
and the sdist (`packages = ["src/pcae"]` in
`[tool.hatch.build.targets.wheel]`; the sdist include-list covers
`src/pcae`). CHGR/Interactive-Workflow JSON Schemas are bundled under
`src/pcae/schema_resources/` (package-relative, ship with the wheel).
The top-level `schemas/repository_intelligence/` directory is
contract/reference documentation only — not loaded at runtime by
`snapshot generate`, and not required for any of the four capabilities
to function from an installed package. No release claim in this
document depends on a repository-only file.

## Known Limitations / Accepted Debt (carried forward, not repaired)

- Empty/missing `agent_id` in an otherwise well-formed governance lock
  is accepted with an empty `producer.kind` string (carried forward
  from `v0.3.1`, harmless, non-authorizing).
- Historical `tasks/DONE.md` sync-debt warnings from `pcae doctor
  task-memory` — pre-existing, repository-maintainer-only, unrelated to
  this release's scope; fresh installed disposable repositories do not
  inherit this debt.
- Shell-gate large-audit-corpus timeout/performance debt — not
  addressed this phase.
- `docs/COMMANDS.md`'s generator does not yet enumerate `pcae runtime
  inspect`, `pcae repository-intelligence`, or `pcae authority
  inspect` as command areas (a pre-existing generator gap, disclosed,
  not fixed — fixing it is a production-source change out of scope for
  this release-hardening phase). `docs/CAPABILITY_REFERENCE_V0_3_2.md`
  is the hand-maintained equivalent for these four capabilities.

## Installation

```bash
git clone <this-repository-url>
cd pcae-harness
pip install -e .
```

or install the wheel/sdist attached to the release.

## Upgrade from v0.3.1

No migration steps required. Every change in this release is
documentation/discoverability plus a version bump; no existing
command's behavior changed, and no new dependency was added.

## Feedback / Next Steps

If you try Repository Intelligence, `pcae runtime inspect`, the
interactive governance workflow, or `pcae authority inspect` against
your own repository and hit friction, please open an issue.
