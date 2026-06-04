# Contributing to PCAE

## 1. Welcome

PCAE (Policy Controlled Autonomous Execution) is a governance-first engineering
framework. Its purpose is to make AI-assisted engineering safe, resumable,
auditable, and human-authoritative — by architecture, not by convention.

Contributions are welcome. Every contribution must preserve the governance
guarantees that PCAE provides:

- Human approval remains authoritative. No contribution may introduce a path
  that bypasses human sign-off.
- Auditability is required. Every execution-relevant change must produce a
  structured record.
- Rollback paths must exist. Write operations require a pre-declared rollback
  plan before execution.
- Runtime trust matters. Runtime contract enforcement must be evaluated before
  any invocation is eligible.
- Evidence is required before execution. Authorization, preflight, audit,
  capture, and review records must all exist before an invocation proceeds.

If a proposed change would weaken any of these guarantees, it falls outside
the scope of what PCAE accepts.

---

## 2. Development Setup

**Clone the repository**

```
git clone <repository-url>
cd pcae-harness
```

**Create a virtual environment**

```
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows
```

**Install dependencies**

```
pip install -e ".[dev]"
```

This installs PCAE in editable mode with all development dependencies,
including `pytest` and `pytest-xdist` for parallel test execution.

**Verify the installation**

```
pcae health
pcae check
python -m pytest -n auto
```

All three must pass before beginning any implementation work.

---

## 3. Contribution Workflow

**Step 1 — Create a task**

Define the scope of your contribution before writing any code. A task
contract specifies which files may be modified and what the session goal is.

For PCAE contributors working inside the repo, use:

```
pcae phase start
```

For external contributors: describe the scope clearly in your pull request.

**Step 2 — Implement the change**

Modify only the files within your stated scope. PCAE enforces architecture
zone dependency rules. Violations are reported by `pcae check`.

**Step 3 — Update documentation**

Documentation is not optional. Every behavior-visible change requires a
corresponding documentation update. See Section 6 for the full list.

**Step 4 — Run validation**

```
pcae health
pcae check
python -m pytest -n auto
```

All three must pass. Do not submit a contribution that fails any of these.

**Step 5 — Submit the contribution**

Open a pull request with a clear description of what changed, why it
changed, and what governance impacts (if any) the change carries.

---

## 4. Governance Requirements

PCAE is a governance framework. Every contribution is held to the same
governance standards that PCAE enforces in the repos it governs.

**Human approval remains authoritative**

No contribution may introduce automatic execution, automatic commit, automatic
push, or automatic rollback. Every action with a consequential outcome requires
explicit human confirmation.

**Auditability is required**

Every invocation-relevant change must produce a structured, machine-readable
audit record. Contributions that remove or weaken audit trail production are
not accepted.

**Rollback paths must exist**

For any contribution that introduces or modifies write-path behavior, a
rollback strategy must be declared and validated before the change is eligible
for merge.

**Runtime trust matters**

Contributions that add new runtime targets, new execution paths, or new
invocation patterns must include a trust assessment. Trust is not assumed.

**Evidence is required before execution**

The PCAE evidence chain — authorization, preflight, audit, capture, review —
must be complete before any invocation is eligible. Contributions that create
execution shortcuts around this chain are not accepted.

---

## 5. Testing Requirements

**Required before every commit**

```
pcae health
pcae check
python -m pytest -n auto
```

`python -m pytest -n auto` is the preferred validation path. It runs all
tests in parallel using `pytest-xdist`, distributing work across available
CPU cores. Tests must be written to be parallel-safe: no shared mutable
state, no hardcoded ports, no filesystem side effects that conflict across
workers.

**Recommended for release-grade verification**

```
python -m pytest
```

This runs the full test suite sequentially without parallelism, providing
additional confidence that test isolation is correct and that no test depends
on execution order.

**Adding tests**

Every new command or behavior change requires corresponding tests. The
minimum bar is:

- At least one test for the happy path
- At least one test for error or edge-case behavior
- Coverage of both human-readable and `--json` output where both exist

Tests that touch governance state (health, check, session, lock) must leave
that state unchanged after the test runs.

---

## 6. Documentation Requirements

The following documentation artifacts must be updated when a contribution
changes behavior that is visible through the PCAE CLI or governance model:

| Artifact | When to update |
|---|---|
| `README.md` | New top-level commands or significant capability additions |
| `docs/whitepaper/PCAE_WHITEPAPER.md` | Architectural changes, new governance domains, or phase-level milestones |
| `docs/architecture/` | Changes to any of the seven governance domains or the execution lifecycle |
| `docs/GOVERNANCE.md` | Changes to governance policies, enforcement rules, or advisory boundaries |
| `CHANGELOG.md` | Every contribution, regardless of size |
| `PROJECT_STATUS.md` | Changes that advance the current phase or alter current capabilities |

Documentation generated by `pcae docs commands --force` must be regenerated
after any CLI change. The generated output must be committed as part of the
same contribution.

---

## 7. Coding Standards

**Maintain backward compatibility**

Existing CLI commands, output formats, and API surfaces must not be silently
changed. If a breaking change is necessary, it must be explicitly documented
and gated behind a new command or flag.

**Avoid hidden automation**

PCAE's core guarantee is that no consequential action occurs without human
awareness. Do not introduce background tasks, deferred writes, implicit
side effects, or auto-repair logic that runs without explicit invocation.

**Preserve governance boundaries**

The seven governance domains (change, rollback, prompt, execution, runtime,
multi-agent, audit/evidence) have explicit boundaries. A contribution that
blurs these boundaries — for example, by having an execution-governance
command modify task-contract state — requires explicit justification and
review.

**Preserve test coverage**

Do not reduce test coverage. If a refactor requires removing tests, replace
them with equivalent tests before removing the original. A contribution that
leaves a command untested is incomplete.

---

## 8. Pull Request Expectations

A pull request is ready for review when:

- **Tests pass.** `pcae health`, `pcae check`, and `python -m pytest -n auto`
  all pass cleanly.
- **Documentation is updated.** Every affected artifact listed in Section 6
  has been updated. `CHANGELOG.md` has a new entry.
- **Governance impacts are documented.** If the contribution changes
  enforcement behavior, adds new execution paths, or modifies the evidence
  chain, the pull request description explains the governance impact and
  confirms that no guarantee has been weakened.

Pull requests that do not meet these criteria will be returned for revision.

---

## 9. License

PCAE is licensed under the Apache License 2.0.

Copyright 2026 Atila Madai

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy
of the License at:

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.

See the [LICENSE](LICENSE) file for the full license text.

By contributing to this project, you agree that your contributions will be
licensed under the same Apache License 2.0.
