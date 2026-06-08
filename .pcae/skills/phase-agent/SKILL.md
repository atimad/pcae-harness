# Skill

## Skill ID

phase-agent

## Skill Name

Phase Agent

## Skill Type

agent

## Skill Version

1.0.0

## Skill Status

active

## Human Review Required

true

## Purpose

Render a complete, agent-ready prompt package for a governed PCAE phase, combining the implementation prompt, validation prompt, governance constraints, safety boundaries, and human review requirements into a single artifact.

## Workflow

1. Resolve the phase target from the roadmap registry.
2. Inspect the capability inventory for the target phase.
3. Render the implementation prompt from registry data.
4. Render the validation prompt from registry data.
5. Compose the agent prompt with governance constraints and safety boundaries.
6. Report completeness score and any rendering signals.
7. Require human review before use.
