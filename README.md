# industry

A self-hosted **EVE Online industry planner**: it syncs everything a
corporation builds with — characters, skills, blueprints, industry jobs,
assets — resolves full production chains against the game's static recipe
data, and (as the planner milestones land) distributes the work across the
roster's skills and build slots.

The data foundation is live and validated against a real corporation; the
planner itself is under active development. See
[`MILESTONES.md`](MILESTONES.md) for the build-out plan and current status.

> [!IMPORTANT]
> **How this project is built.** This repository is developed with an
> agentic SDLC: the human acts as product owner — providing the vision,
> priorities, and domain understanding of how the system should work —
> and AI agents act as the junior developers who implement solutions in
> priority order. Every change is reviewed and approved by the product
> owner before it is merged. If you have a fundamental objection to
> AI-assisted software development, this project informs that choice up
> front: you are free to not consume or contribute to it.

## Where it's going

The end goal is a **work-distribution planner** for a single corporation
and its registered characters. You input a target build and quantity; the
system reverses the product chain to raw-material inputs, then rebuilds
every layer — distributing jobs across characters based on skill
availability and chunking them across build slots so each stage's inputs
complete as fast as possible. Parallelism comes from **BPC copies**: the
planner recommends how many copies to make from owned BPOs and each one's
run count. A **profit-vs-throughput slider** biases the distribution
between material efficiency (fewer, larger jobs on the best-skilled
builders) and time-to-completion (every slot filled).

Capability analysis closes the loop on the roster itself: matching synced
skills and blueprints against the buildable catalog, recommending targets
the corporation is positioned to produce and surfacing per-target gaps
with three responses — train, farm out as paid contracts, or pick a
better target.

The calculation core is already proven out as executable reference
implementations ([`reference/`](reference/)) whose golden values are
captured in [`TYPHOON-CHAIN.md`](TYPHOON-CHAIN.md) — the fully expanded
Typhoon production chain with scheduling and BPO-recommendation models
the milestones graduate into the app.

## What works today

- **EVE SSO is the only login.** No local accounts. Signing in sends you
  to `login.eveonline.com`; each pass through "Add character" authorizes
  one more character (across multiple EVE accounts), with background
  token refresh for all of them.
- **Character industry data, synced.** Assets, blueprints (with ME/TE and
  run counts), skills (trained and active levels — active includes
  implants/boosters), and industry jobs — current and historical — pulled
  into the local database on a background schedule or on demand, and
  served from stored data only (page renders never touch ESI).
- **Main character & corporation pool.** One character is flagged as the
  main; its corporation becomes the shared pool. A Director/CEO role gate
  (with explanatory states, never error spam) guards the Corporation
  section: corp assets, blueprints, and industry jobs, with rented
  offices surfaced as the corporate inventory locations.
- **SDE recipe mirror.** Blueprint recipes (materials, products, skills,
  durations) come from the EVE static data export, not ESI: the `sde_*`
  tables are a **verbatim mirror** of the fuzzwork SQLite dump, checked
  and re-imported automatically when a release changes, with manual
  controls under **Admin → SDE Data**.
- **Location naming everywhere.** Stations, structures, and office
  containers resolve to real names at sync time through a universe
  resolver; structures your characters can't dock in park as
  `Structure #<id>` without burning ESI's error budget.

Everything is plain SQL joins away from the planner: owned blueprints,
per-character skills, and installed jobs sit in owner-keyed tables
alongside the recipe mirror.

## Architecture: three data layers

Every planner feature is a join across exactly these layers — the split
is what lets T2/T3 invention and reactions arrive later as data and
resolver extensions instead of schema rewrites.

| Layer | Source | Nature |
|---|---|---|
| **Static (recipes)** | EVE SDE, imported | Write-once per release: blueprint → materials, products, skills, durations |
| **Dynamic (world state)** | ESI, ETag-cached sync | Refreshed in background: owned blueprints, skills, jobs, assets |
| **User state** | This app | User-managed: main character, structures, build plans |

## Register an EVE application

1. Create an application at <https://developers.eveonline.com>.
2. Callback URL: `http://localhost:8000/auth/eve/callback` — it must match
   `ESI_CALLBACK_URL` byte-for-byte (localhost ≠ 127.0.0.1; no trailing slash).
   For a public deployment use your `https://` URL and update `.env`.
3. Select the scopes listed in `.env.example` (`ESI_SCOPES`). Changing scopes
   later requires re-authorization.
4. Copy the Client ID and Client Secret into `.env`.

## Local development

Development and testing run inside a local container — no local dependency
installs. The only host requirements are `uv` (to build) and a container
runtime with compose (`podman compose` on Fedora, or `docker compose`).

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)

podman compose -f compose.dev.yml up dev
```

Open <http://localhost:8000>, sign in, and you should land on the dashboard
with your character's portrait and wallet balance — proving the full
OAuth code → token → ESI call chain.

How it works:

- The repo is bind-mounted at `/app` inside the container, so code edits
  pick up immediately via `--reload` — no rebuild needed.
- All dependencies (including dev tools) are baked into the image's `dev`
  stage with the venv at `/opt/venv`; rebuild with
  `podman compose -f compose.dev.yml build dev` only after changing
  `pyproject.toml` or `uv.lock`.
- The dev database is `industry.db` at the repo root, shared with the
  pre-container workflow — authorized characters carry over.
- Under rootless podman, the container runs as root mapped to your user,
  so files it writes into the mount (caches, the DB) keep host ownership.

### Tests, lint, migrations

All inside the same container:

```sh
podman compose -f compose.dev.yml run --rm dev pytest
podman compose -f compose.dev.yml run --rm dev ruff check .

# migration cycle against a throwaway database
podman compose -f compose.dev.yml run --rm dev sh -c \
  'DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic downgrade base && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head'
```

### EVE static data (SDE)

The `sde_*` tables are created and replaced wholesale by the import (no
app-side migration; dump schema changes can't break it). The import checks
the published dump MD5 first and exits without downloading when the
release is unchanged. A background loop performs the same check at most
once a day and re-imports on change; **Admin → SDE Data** shows the last
check, last import, and outcome, with a manual Check now. Safe to run by
hand any time:

```sh
podman compose -f compose.dev.yml run --rm dev python -m app.sde import
podman compose -f compose.dev.yml run --rm dev python -m app.sde info
```

### Direct uv alternative

The container is the supported path, but the plain-uv workflow still works
if a container runtime is unavailable: `uv sync`, then `uv run` for the
commands above.

## Docker

```sh
docker compose up --build      # or: podman compose up --build
```

The image is multi-stage: the default (production) target ships only
runtime dependencies and the app code; the `dev` target used by
`compose.dev.yml` adds the dev toolchain. The SQLite database lives in
`./data/` (bind-mounted to `/data` in the container) and survives restarts.
Migrations run automatically on start.

## Security notes

- This is a **personal tool**: anyone who can reach the app and logs in with
  their own EVE account can see all stored characters. Keep it on localhost
  or behind an access restriction (VPN, reverse-proxy auth) when deployed.
- The session cookie is signed with `SECRET_KEY`; tokens never leave the
  database.
