# industry

A self-hosted **EVE Online industry planner**: it syncs everything a
corporation builds with — characters, skills, blueprints, industry jobs,
assets — resolves full production chains against the game's static recipe
data, and (as the planner milestones land) distributes the work across the
roster's skills and build slots.

**Documentation**: <https://blitz-tools.github.io/industry/>

- [Administration](https://blitz-tools.github.io/industry/admin/installation/) —
  standing the app up: EVE SSO registration, environment, containers, SDE
  data, security.
- [Development](https://blitz-tools.github.io/industry/development/getting-started/) —
  the containerized workflow, testing and linting, project process,
  architecture.
- [User guide](https://blitz-tools.github.io/industry/user-guide/characters/) —
  signing in, characters and the roster, asset browsing, blueprints,
  skills, jobs, and the Corporation section.

> [!IMPORTANT]
> **How this project is built.** This repository is developed with an
> agentic SDLC: the human acts as product owner — providing the vision,
> priorities, and domain understanding of how the system should work —
> and AI agents act as the junior developers who implement solutions in
> priority order. Every change is reviewed and approved by the product
> owner before it is merged. If you have a fundamental objection to
> AI-assisted software development, this project informs that choice up
> front: you are free to not consume or contribute to it.

**Branch protection.** `main` is protected by a ruleset: everything
lands through pull requests passing required status checks — code
changes run the test suite and CodeQL analysis, documentation-only
changes run the docs/config lint job. Nothing merges ungated, and no
one (including the owner) bypasses the rules.

## Quick start

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)

podman compose -f compose.dev.yml up dev
```

Signing in needs an EVE SSO application registered first — see the
[installation guide](https://blitz-tools.github.io/industry/admin/installation/)
for the full path.

## Planning surfaces

- [`MILESTONES.md`](MILESTONES.md) — the milestone build-out plan, with
  status and validation steps.
- [`TODO.md`](TODO.md) — smaller items and ideas.
- [`reference/`](reference/) — the planner's proof-out scripts and
  [`reference/chains/`](reference/chains/) chain documents
  (`TYPHOON-CHAIN.md` is the golden-values reference for the standing
  validation case).
