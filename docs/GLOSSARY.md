# PCAE Governance Glossary

## active task

The single task contract currently governing a work session. `pcae check` enforces
scope restrictions drawn from the active task. Only one task may be active at a time.

## agent lock

A local lease file (`.pcae/agent-lock.json`) that records which agent is performing
governed work. Prevents accidental concurrent agent sessions in the same repository.
Acquired with `pcae agent acquire` and released with `pcae agent release`.

## allowed files

A set of file paths declared in the active task contract that the agent is permitted
to read or modify. `pcae check` reports a violation if a file outside this set is
touched during the session.

## allowed zones

Named directory prefixes declared in the active task contract. Files under an allowed
zone are implicitly permitted. Zones provide coarser-grained scope control than
individual allowed files.

## architecture history

A local append-only log (`.pcae/architecture-history.json`) of architecture check
snapshots. Each entry records zone counts, rule violations, enforcement mode, and
timestamp. Read by `pcae analytics` and `pcae architecture metrics`.

## architecture rules

Constraints declared in `policy.toml` that govern module boundaries, import
directions, or file placement within architecture zones. Violations are recorded in
architecture history and surfaced by `pcae check`.

## architecture zones

Named directory regions defined in `policy.toml` that partition the repository into
logical modules (e.g. `src/`, `tests/`, `docs/`). Rules are expressed in terms of
zones. `pcae architecture snapshot` classifies files into zones at check time.

## CI drift

A divergence between the generated `.github/workflows/pcae-governance.yml` and the
canonical workflow content expected by the current harness version. Detected by
`pcae ci drift` and repaired by `pcae ci repair`.

## CI repair

The act of regenerating the GitHub Actions governance workflow to eliminate CI drift.
`pcae ci repair --dry-run` previews the repair; `pcae ci repair --force` writes it.

## daemon dry-run

A simulated single monitoring cycle executed by `pcae daemon run --dry-run`. Reports
which governance checks would run without starting a persistent process or writing
files.

## enforcement mode

A policy setting (`advisory` or `strict`) that controls how `pcae check` treats
violations. In `advisory` mode violations are reported but do not cause a non-zero
exit. In `strict` mode any violation causes the check to fail.

## fleet drift

A divergence in governance state detected across one or more repositories in the fleet
registry. `pcae fleet drift` aggregates per-repo drift signals and reports which repos
require attention.

## fleet registry

The local list of governed repository paths stored in `.pcae/fleet.json`. Managed
with `pcae fleet add`, `pcae fleet list`, and `pcae fleet remove`. Used by all
`pcae fleet` subcommands.

## forbidden files

File paths explicitly excluded by the active task contract. Touching a forbidden file
during a session is a scope violation regardless of allowed-zone declarations.

## forbidden zones

Named directory prefixes explicitly excluded by the active task contract. Files under
a forbidden zone are out of scope even if they would otherwise be permitted by an
allowed-zone declaration.

## governance bundle

A portable JSON export of current governance state produced by `pcae export bundle`.
Contains policy, task contracts, session snapshot, and architecture history. Can be
imported into another repository with `pcae import bundle`.

## governance health

A summary of whether a repository meets all PCAE readiness criteria. Reported by
`pcae health` (human-readable) or `pcae health --json` (machine-readable). Aggregates
policy validity, active task presence, session continuity, and agent lock state.

## governance risk

A computed score summarizing the likelihood of governance degradation based on
architecture history trends. Reported by `pcae analytics risk`. Higher scores indicate
accumulating drift, stale tasks, or repeated enforcement violations.

## governance runtime

The set of local files and processes that enforce PCAE governance: `policy.toml`,
task contracts, session snapshots, architecture history, and the `pcae check` and
`pcae health` commands. The runtime operates entirely within the repository without
external services.

## pipeline dry-run

A preview of a named governance workflow produced by `pcae pipeline run --dry-run`.
Reports which checks and exports would execute without writing operational artifacts
or advancing session state.

## session continuity

A property verified by `pcae check` confirming that a valid session snapshot exists
and that the current agent context matches the recorded session. Broken continuity
indicates a session was not properly started or was interrupted without being finalized.

## task contract

A structured TOML file in `tasks/active/` that defines the scope, goal, allowed
files, forbidden files, allowed zones, forbidden zones, and enforcement mode for a
unit of governed work. Created with `pcae task new` and consumed by `pcae check`.
