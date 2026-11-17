# Workflow

## Agentic SDLC

This repository is developed with an agentic SDLC: the human acts as
**product owner** — providing the vision, priorities, and domain
understanding of how the system should work — and AI agents act as the
junior developers who implement solutions in priority order. Every change
is reviewed and approved by the product owner before it is merged.

The planning surfaces live in the repository:

- [`MILESTONES.md`](https://github.com/blitz-tools/industry/blob/main/MILESTONES.md)
  — the milestone build-out plan with status and validation steps.
- [`TODO.md`](https://github.com/blitz-tools/industry/blob/main/TODO.md)
  — smaller items and ideas, each with enough context to pick up in a
  fresh session.
- [`TYPHOON-CHAIN.md`](https://github.com/blitz-tools/industry/blob/main/TYPHOON-CHAIN.md)
  and [`reference/`](https://github.com/blitz-tools/industry/tree/main/reference)
  — the planner's golden values and proof-out scripts.

## Branch protection

`main` is protected by a ruleset: everything lands through pull requests
passing required status checks — code changes run the test suite and
CodeQL analysis, documentation-only changes run the docs/config lint
job. Nothing merges ungated, and no one (including the owner) bypasses
the rules.

The required checks:

- `Detect changes (CI)` / `Detect changes (CodeQL)` — the PR classifier
  (a failed classifier blocks the merge rather than silently skipping
  everything).
- `Lint docs & config` — markdown lint, YAML lint, strict docs build; on
  every PR.
- `test` — ruff, pytest, migration cycle; on code changes.
- `Analyze (actions)` / `(javascript-typescript)` / `(python)` — CodeQL;
  on code changes.

## The change flow

1. Branch from `main`.
2. Implement, verifying in the dev container (see
   [testing](testing.md)).
3. Open a pull request. CI classifies it and runs the applicable checks.
4. Product-owner review — approval is per-change, never standing.
5. Merge once green. Direct pushes to `main` are not possible; force
   pushes and deletions are blocked.

Commit messages and PR descriptions should explain *why* — the planning
documents carry the what.
