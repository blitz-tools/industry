# Testing and linting

All inside the same dev container:

```sh
podman compose -f compose.dev.yml run --rm dev pytest
podman compose -f compose.dev.yml run --rm dev ruff check .

# docs and config linting (the same checks CI runs on every PR)
podman compose -f compose.dev.yml run --rm dev uv run yamllint .
podman compose -f compose.dev.yml run --rm dev \
  uv run pymarkdownlnt --config .pymarkdownlnt.yml scan .

# docs site build (strict — fails on broken links or bad config)
podman compose -f compose.dev.yml run --rm dev \
  uv run --group docs zensical build --strict

# migration cycle against a throwaway database
podman compose -f compose.dev.yml run --rm dev sh -c \
  'DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic downgrade base && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head'
```

## What each check covers

- **pytest** — the full suite (ESI client hardening, syncs, pages,
  migrations, auth). Every ESI interaction is mocked with respx; the
  clock is injectable for time-dependent tests.
- **ruff** — linting with line length 90, targeting Python 3.12.
- **yamllint** — the GitHub workflows and compose files, tuned via
  `.yamllint` (line length off, GitHub's `on:` key allowed).
- **pymarkdownlnt** — every markdown file in the repo, tuned via
  `.pymarkdownlnt.yml` (line length and emphasis-as-heading off, matching
  the established doc style). Run it with `--config .pymarkdownlnt.yml`;
  the default config lookup is unreliable.
- **zensical build --strict** — the documentation site, catching broken
  internal links and config errors before deploy.
- **migration cycle** — `upgrade head` → `downgrade base` →
  `upgrade head` proves migrations run in both directions on a fresh
  database.

## How CI applies these

On every pull request:

- `Lint docs & config` runs the markdown lint, YAML lint, and the strict
  docs build.
- A `changes` job classifies the PR: documentation-only changes skip the
  heavy jobs (reporting "Skipped", which the required checks treat as
  passing); anything touching code runs `test` (ruff, pytest, migration
  cycle) and CodeQL analysis.

## Docs tooling notes

The site builds with **Zensical** (the maintained successor of Material
for MkDocs, from the same team, MIT-licensed) using its MkDocs
compatibility mode: it reads the same `mkdocs.yml`, and its `classic`
theme preserves the Material appearance. Material for MkDocs reached end
of life on May 5, 2027, which is why the new site started on Zensical.

MkDocs + Material stay in the `docs` dependency group as a fallback —
the project builds under either tool (`mkdocs build` works if Zensical
ever misbehaves).

The deployed site is built from `main` by the `Docs` workflow whenever
`docs/` or `mkdocs.yml` changes.
