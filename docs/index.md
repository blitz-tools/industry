# industry

A self-hosted **EVE Online industry planner**: it syncs everything a
corporation builds with — characters, skills, blueprints, industry jobs,
assets — resolves full production chains against the game's static recipe
data, and (as the planner milestones land) distributes the work across the
roster's skills and build slots.

The data foundation is live and validated against a real corporation; the
planner itself is under active development.

## What it does today

- **EVE SSO is the only login.** No local accounts. Each pass through
  "Add character" authorizes one more character — across multiple EVE
  accounts — with background token refresh for all of them.
- **Character industry data, synced.** Assets, blueprints (with ME/TE and
  run counts), skills (trained and active levels), and industry jobs —
  current and historical — pulled into the local database on a background
  schedule or on demand, and served from stored data only: page renders
  never touch ESI.
- **Main character & corporation pool.** One character is flagged as the
  main; its corporation becomes the shared pool. A Director/CEO role gate
  guards the Corporation section: corp assets, blueprints, and industry
  jobs, with rented offices surfaced as the corporate inventory locations.
- **SDE recipe mirror.** Blueprint recipes come from the EVE static data
  export, not ESI: a verbatim mirror of the fuzzwork SQLite dump, checked
  and re-imported automatically when a release changes.
- **Location naming everywhere.** Stations, structures, and office
  containers resolve to real names at sync time; structures your
  characters can't dock in park as `Structure #<id>` without burning
  ESI's error budget.

## Where it's going

The end goal is a **work-distribution planner**: input a target build and
quantity, and the system reverses the product chain to raw-material inputs,
then rebuilds every layer — distributing jobs across characters based on
skill availability, chunking them across build slots via BPC copies, and
biasing the split between material efficiency and time-to-completion with
a plan-level slider. Capability analysis then closes the loop on the
roster itself, recommending what the corporation is positioned to build
and surfacing per-target gaps.

The roadmap lives in
[`MILESTONES.md`](https://github.com/blitz-tools/industry/blob/main/MILESTONES.md)
in the repository, with the Typhoon production chain as the standing
validation case
([`TYPHOON-CHAIN.md`](https://github.com/blitz-tools/industry/blob/main/reference/chains/TYPHOON-CHAIN.md))
and the calculation core proven out as reference implementations in
[`reference/`](https://github.com/blitz-tools/industry/tree/main/reference).

## Guide sections

- [Administration](admin/installation.md) — standing the application up:
  EVE SSO registration, environment, containers, SDE data, security.
- [Development](development/getting-started.md) — the containerized
  workflow, tests and linting, the project's process, and architecture.
- [User guide](user-guide/characters.md) — signing in, characters and the
  roster, asset browsing, and the Corporation section.
