# PCAE v0.3.1 Release Notes (Release Candidate)

## Overview

v0.3.1 is a patch release. It completes the generic external-agent
intake path `v0.3.0` introduced by removing its last remaining
friction point — a required tool-specific adapter script — and adds
`codex-ox` as a second, concrete example of a governed non-Claude
agent/session identity. No CLI surface, JSON schema, or authority
semantic changes; every `v0.3.0` command and behavior is unchanged.

## Added / Improved

- **`pcae intake from-files`** — a packaged, generic CLI command that
  builds and submits an Intake Candidate directly from local file
  changes, for any producer, with no adapter script required.
  `scripts/claude_code_intake_adapter.py` (the `v0.3.0` reference
  adapter) is now a thin, deprecated wrapper over this same command;
  it remains repository-only (not part of the installed package).
- **Session/governance-lock descriptive producer provenance** — when a
  PCAE governance agent lock is held (`pcae session bootstrap
  --agent-id <id>`), `pcae intake from-files` derives `producer.kind`
  from it automatically instead of requiring a repeated `--producer`
  flag. This is descriptive metadata only — it is never an
  authorization or authentication claim, and never affects acceptance,
  promotion, or execution authority.
- **`codex-ox`** — a first-class PCAE agent/session identity
  (capability registry, agent-config registry, session-bootstrap
  recognition, governance-lock provenance, generic intake
  compatibility). This does **not** mean PCAE executes Codex through
  Ox/OpenRouter — there is no PCAE-native execution backend, network
  transport, or provider/model authentication behind this identity;
  runtime posture remains `Observed` / `observe` / `unavailable`.
- **Quickstart golden path updated** — `docs/QUICKSTART_V0_3.md` now
  leads with `pcae intake from-files` as the primary, packaged path
  for every producer (Claude Code included); the legacy adapter script
  is demoted to a clearly marked reference footnote.
- **Malformed-agent-lock hardening** — `pcae intake from-files` and
  `pcae session bootstrap` previously crashed with an uncaught
  exception (a raw Python traceback) when `.pcae/agent-lock.json` was
  present but corrupted: invalid JSON (`v0.3.0`-era finding, repaired
  in Phase 149O.20L.7O.2Y), and separately, well-formed JSON that
  decodes to a non-object value such as an array, string, number, or
  null (independently found and repaired in this release-candidate
  verification phase, 149O.20L.7O.2Z). Both now fail closed with a
  clean, deterministic rejection — no traceback, no repository
  mutation, no authority granted, and no silent fall-through to the
  no-lock/explicit-`--producer` path.

## Compatibility

- **Direct/unbootstrapped generic intake remains supported.**
  `pcae intake from-files --producer "<any-string>"` works with no
  governance agent lock held, identical to `v0.3.0`'s adapter-script
  `--producer` behavior. Bootstrap is convenience, not a requirement.
- **Arbitrary/custom producer identities remain supported.** Any
  string is accepted as `producer.kind`; registry membership is never
  required.
- **Stable `v0.3.0` governance semantics preserved.** Task-scope
  authority, repository/base-commit binding, content-hash validation,
  and the review/promotion/rollback chain are unchanged.

## Explicit Boundaries

- **Producer provenance remains descriptive.** `producer.kind` is a
  label, never a verified identity or an authorization signal.
- **No producer authentication.** Neither the governance lock nor
  `--producer` is cryptographically or otherwise verified.
- **No Codex-Ox execution backend.** `codex-ox` cannot be dispatched
  for subprocess invocation (`_build_invoke_command("codex-ox", ...)`
  returns `None`); it is excluded from the runtime-probe and
  subprocess-invocation paths entirely.
- **No OpenRouter transport.** No network call, API key, or endpoint
  configuration is required or performed to register or bootstrap
  `codex-ox`.
- **No native model-specific parser** for any producer (Claude, Codex,
  Codex-Ox, or otherwise) — the intake contract remains generic JSON.
- **Runtime execution remains unavailable.** `pcae runtime inspect`:
  `execution_capability: unavailable`, unchanged since `v0.2.0`.

## Package Boundary

`pcae.core.agent`, `pcae.core.intake`, `pcae.commands.intake`,
`pcae.commands.session`, and `pcae.cli`'s `intake from-files` wiring
are all packaged in both the wheel and sdist. The legacy
`scripts/claude_code_intake_adapter.py` reference script and
`docs/QUICKSTART_V0_3.md` remain repository-only (GitHub-hosted, not
package data) — no release claim in this document depends on either
being installed.

## Known Limitations

Carried forward from `v0.3.0`, unchanged: text/`content_after`-only
intake (no diff/patch or binary support); scoped to the single active
governed task; not published to PyPI; a documented, non-exploitable
Windows-path admission gap in the intake layer; repository fingerprint
is a content hash, stable across clones/forks of identical history, not
a location-unique identifier.

New, accepted as technical debt: an empty or missing `agent_id` in an
otherwise well-formed governance lock is accepted with an empty
`producer.kind` string — a harmless, uninformative provenance label. It
cannot impersonate any registered identity (`get_agent_by_id("")`
returns `None`) and never affects authority.

## Installation

```bash
git clone <this-repository-url>
cd pcae-harness
pip install -e .
```

or install the wheel/sdist attached to the release.

## Upgrade from v0.3.0

No migration steps required — every change in this release is
additive or a bounded bug fix; no existing command's behavior changed.

## Feedback / Next Steps

If you try `pcae intake from-files` or `codex-ox` bootstrap against
your own repository and hit friction, please open an issue.
