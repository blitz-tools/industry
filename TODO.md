# TODO / Roadmap

Work noted for later, and future ideas. Each item carries enough context
(the "why", the relevant code, and known prerequisites) to start on it in a
fresh session without re-deriving the design. Move items to a short "in
flight" note or just delete them when they land; keep details here rather
than in commit history — this file is the planning surface.

Groundwork that already exists and applies broadly:

- **Owner-keyed schema**: `characters` / `assets` rows carry
  `owner_type`/`owner_id`; the asset sync and `UniverseResolver`
  (`app/esi/universe.py`, `app/esi/assets.py`) are owner-agnostic, so
  corporation data reuses them unchanged.
- **ESI (EVE Swagger Interface) client**: ETag-cached GETs with
  per-character token refresh
  (`app/esi/client.py`). Scope-gated calls only — scopeless calls are
  guaranteed 403s and burn ESI's error-limit budget.
- **Registered portal scopes** (see `.env.example` `ESI_SCOPES`): character
  and corporation variants of assets, blueprints, industry jobs, market
  orders, wallets, projects, skills, skill queue, location.
- **Synced industry data** (M1 + M2, PRs #12–#17): the owner-keyed
  `blueprints`, `skills`, and `industry_jobs` tables hold both sides —
  corporation (main's corp) and every registered character — refreshed
  by the background sync with per-kind status in `data_syncs`. The
  planner's owned-blueprint overlay, skill math, and job correlation
  are plain DB joins now, no new fetching.
- **Location naming**: `UniverseResolver.resolve_location_ids`
  (`app/esi/universe.py`) names any location id that arrives without a
  usable type — blueprint locations, job stations, dangling item ids —
  classifying by id range (stations < 10¹² answer on the public
  stations endpoint; structures/office containers on the scoped
  structures endpoint) and parking unresolvable ids as restricted. Any
  new surface that shows a Location should resolve through it at sync
  time; renders stay pure `universe_locations` joins.
- **Assets page purity rule**: page renders never touch ESI; everything
  resolves through the background sync into DB tables first.
- **UI patterns to reuse**: collapsible rows/cards with sync-state rings
  (assets toolbar), notification boxes (`CardIssue`), in-place content
  swaps (`swapAssetsPage` in `app/static/app.js`), remembered open/closed
  state via localStorage (`corp-rows.js`), compact icon buttons for
  row/card-level actions (`.icon-button` in `app/static/style.css` —
  preferred over boxed text buttons for repeated item-level actions;
  page-level actions keep the boxed style).

---

## In queue

- **Container custom names sync — `asset_names` + `ESIClient.post()`**
  (the M6 loose end, deferred from the markings PR and recorded here
  2026-11-25): the plans surfaces scope material sources per container,
  but containers render by type name ("Station Container · Amamake")
  because custom names never sync. The schema exists (migration 0011's
  `asset_names` table: owner key + item_id + name). The work: a small
  `post()` on `ESIClient` beside `get()`, then a best-effort
  `POST /characters/{id}/assets/names/` pass after the asset snapshot
  replaces (outside the snapshot write, so a failed fetch keeps old
  names). **Gotcha** (PR #52 investigation): a batch containing any
  never-named item id fails wholesale with 404 "Invalid IDs in the
  request" — the pass must fall back per item, with a retry cap (the
  error-budget discipline). Names are free text (one live container is
  literally "None") and render verbatim. Natural home: M9's job
  allocation (containers as work locations), or whenever container
  labels start misleading in practice.
- **Blueprint → plan chip** (owner note, 2026-11-24): from the blueprints
  surfaces, a chip that loads a blueprint into a plan — a **BPC loads at
  its max target** (remaining runs × products-per-run units), a **BPO
  loads at 1 target** (unlimited runs, so the count is the owner's to
  step up). The chip deep-links into the planner with the product
  target and quantity pre-filled (commodity-first; run math is
  computed, never asked). Pickup calls: which surface carries the chip
  (the character/corp blueprints pages, the planner's owned-copies
  overlay, or both) and whether it targets the bare planner or the
  M6 export flow. Once M15's market data lands, the same rows gain
  **estimated price per unit at `<market_hub>` sell** and **estimated
  profit/loss** computed against the hub's buy / split / sell rates
  (M10's build-vs-buy math supplies the verdict shape). A companion
  chip **builds a skill plan for the blueprint** (M13's calculator) or
  states that **all required skills are already held** — the
  eligibility check the planner's skill gate already computes, surfaced
  per blueprint.
- **Ancient Relics acquisition sources** (owner note, M5 review
  2026-11-24): the acquisition table's "Acquire via" column pins each
  terminator category to its in-game mechanic; the relic category
  (and the salvage families) currently read "Market" via the fallback.
  Investigate their real sourcing (wormhole site drops, sleeper
  relic sites, contract markets) against M15's synced data and
  community documentation, then extend `_RAW_ACQUIRE` in
  `app/routes/planner.py` — relics enter the planner through M8's
  invention overlay, so the pin can land with that milestone.

*(Documentation site landed 2026-11-17: mkdocs-material under `docs/`,
deployed to GitHub Pages by the `Docs` workflow; README links to the
site. Keep pages near the code they document and update them alongside
milestone work so they drift slowly.)*

---

## Industry planner track

**Folded into the milestones (2026-11-22, final pre-implementation
refinement)**: the planner-track sections that lived here — the
structure-manager, planner, and build-plans specs; the multibuy
export; station-container bucketing; the LP-stores investigation;
the M5 expander harness; contract-match fallbacks; the skill-plan
calculator; assignment eligibility; the navbar refinement — are
absorbed by their owning milestones (M3, M4/M5, M6, M13, M15, M16),
with the M6 five-item triage recorded in MILESTONES.md. This file
now carries the platform track and smaller items only.

## Platform / administration

### Observability — central page, storage, tracing

(direction 2026-11-22, from the M15 sync-panel design)

- **Admin > Observability** is the central page: all available
  observability data in one place — sync status per family, ESI
  rate-limit and error budgets per route group, sync/job durations,
  staleness per table. Specific pages show a **subset** (the Markets
  sync panel shows its families and rate-limit headroom; the
  structures page its sync-source lines) but the checks are **never
  duplicated** — one stored dataset, page-filtered views, the
  central page authoritative.
- **Storage**: telemetry stored locally by default; exportable to
  third-party storage domains — **Prometheus, Loki, Thanos**, or
  other open-source observability applications. **No coalescing
  layer** (owner decision, 2026-11-25): the append-only
  `rate_limit_observations`/`sync_runs` tables ARE the time series at
  raw resolution (7/30-day retention) — don't build aggregation before
  an exporter exists; add one only if a local over-time view is needed
  first. The eventual exporter maps cleanly onto Prometheus metric
  types (<https://prometheus.io/docs/concepts/metric_types/>):
  **gauges** for per-group remaining/max/percentage-of-window and the
  error-budget remainder (the values float up and down — counters
  would be wrong), **histograms** for per-request token costs and
  sync-run durations (the `_count` series covers run totals).
- **SQLite (database) health** (owner note, 2026-11-25): storage usage,
  response times, and row counts on the central page. Landed with the
  slice: page/file storage (WAL file included) and per-table row
  counts, read live at render (`sqlite_stats` in `app/db.py` — no
  schema, renders stay side-effect-free). Still future: **query
  response times** — instrument via SQLAlchemy engine event hooks
  (`before_cursor_execute`/`after_cursor_execute` in-memory
  accumulators, snapshotted on the background tick like the sync-run
  durations) plus slow-query logging. The headroom signals to watch,
  per SQLite best practice: freelist fraction of the file (a VACUUM
  candidate), WAL growth (checkpoint health), and busy/write-lock
  contention — the app runs concurrent background ticks plus request
  renders against one file, and `journal_mode=WAL` is the standard
  mitigation (today's engine sets only `PRAGMA foreign_keys=ON`;
  switching journal modes is a deployment decision to make
  deliberately).
- **Code tracing for future debugging** (future work): implement
  via **OpenTelemetry (OTEL)** where possible — request/job spans
  extending the metrics conventions M15 already records (zero-code
  Python instrumentation; the uv bootstrap caveat is documented in
  MILESTONES.md's M15 note).

### Managed release updates — pull from GitHub Releases, migrate in place

(owner note, 2026-11-25)

The project will run with releases, and DB migrations are a real portion
of the upgrade effort between them — the schema moves with every
milestone (0013 observability telemetry is the latest), and a deployment
that lags `alembic upgrade head` breaks on the first new-table read
(the dev deployment's 500 on `/admin/sync`, 2026-11-25, was exactly
this). Wanted: a **managed update process** that, after a release is
published, pulls it in and brings the deployment up cleanly in place:

- **Pull from GitHub Releases**: fetch the published release (versioned
  artifacts or tag) — not a git checkout — and stage it beside the
  running deployment (the container image / compose stack is the
  deployment shape to build on; `compose.dev.yml` is today's only
  compose file, so a production compose profile arrives with this).
- **Managed DB migration step**: run `alembic upgrade head` as part of
  the update flow itself, never left to the operator's memory — the
  up/down/up cycle convention (CI-proven per release) is the safety net
  the release process leans on. Migration ordering constraints and
  hand-written-migration notes live with the alembic versions.
- **Clean in-place cutover**: backup the SQLite database before
  migrating, apply the update, restart, and verify with a health check
  (the Observability page's sync-status read is a natural post-update
  verification surface) with a documented rollback path (restore
  backup + previous release).
- Prerequisites to settle first: a release pipeline producing versioned
  GitHub Releases (CI already builds and tests per PR; the release
  artifact shape is the missing piece), a pinned-version production
  deployment target, and a decision on how the updater runs (a small
  update script/command wrapping compose, vs. something like
  watchtower-style automation — start manual-but-managed).

### Local user accounts + admin menu

Today the app is single-user (EVE SSO is the only login; the session just
holds an "authenticated" flag — see `is_authenticated` in `app/deps.py`).
Prerequisite work for anything multi-user:

- Local user accounts; the first account created during install is admin
  level.
- Characters become owned by accounts (migration + ownership checks on
  routes/sync).
- Admin menu (visible when logged in as admin) with sub-sections:
  - **Account management**: add, delete, update, manage accounts.
  - **Dashboard**: total users, character count, active users, logins
    (7 days), new users this week/month, logged-in last 24 h.
  - **Observability / health**: database health (connections, query
    counts, errors), ESI health (requests, errors, 401/403/404 counts,
    error-limit budget), logging levels (info/debug/warning/error).
  - **System settings / controls**.
- Deployment note: an access restriction in front of the app remains
  required wherever it is exposed (SSO-only login today).

### Licensing & legal notices (CCP + open source)

(per product direction, 2026-11-20)

The app uses ESI, EVE SSO, the SDE mirror, and EVE image assets —
all under CCP's Developer License Agreement, which requires
preserving CCP's IP notices. The repo already ships a **GPLv3
LICENSE**; this item aligns everything around it.

1. **CCP proprietary notice — UI footer / About screen** (app base
   template's footer; the mockups' `.sidebar-footer` is the shape):
   - Standard copyright & trademark footer:
     *"© 2014–2026 CCP hf. All rights reserved. "EVE", "EVE Online",
     "CCP", and all related logos and images are trademarks or
     registered trademarks of CCP hf."*
   - Non-affiliation disclaimer alongside it:
     *"soliton is an independent third-party application and is not
     affiliated with, endorsed, or sponsored by CCP hf."*
2. **Open-source repository & distribution notices**:
   - Amend the GPLv3 **LICENSE** (or add a preamble note) stating it
     covers the source code only and grants no open-source rights to
     CCP's copyrighted game data, icons, or trademarks.
   - **Third-party dependency notices** (THIRD_PARTY_NOTICES file or
     an About page): the copyright notices and license texts of the
     open-source dependencies — generated via `pip-licenses`
     (Python); relevant because Docker images and bundled web assets
     are distributed. **Repo-specific**: the app also renders images
     from `images.evetech.net` (community image proxy) — include it
     in the attribution review.
   - **Self-hosting note in README.md**: anyone deploying their own
     public instance with their own EVE SSO client ID must accept
     CCP's Developer License Agreement themselves on the EVE
     Developers Portal — say so explicitly to save contributors
     confusion.
3. **Additional disclosures (if applicable)**:
   - **Privacy policy** (applies — the app stores character IDs,
     refresh tokens, and ESI data): a footer link explaining what
     data is stored, how tokens are secured, and how users revoke
     access or delete their data (the forget/revoke flows already
     exist).
   - **Donation / ad disclaimer**: only if donations or ads are ever
     accepted — voluntary donations must not unlock gated features
     (CCP Developer License FAQ).

---

## Smaller items / ideas

- **Workflow documentation screenshot pass** (owner direction,
  2026-11-24): `docs/user-guide/workflows.md` carries the intended
  workflows with per-section figure slots (marked *pending the
  screenshot pass*); the pass itself needs a capture pipeline — a
  headless-browser script that walks each workflow, highlights the
  active control (an outline overlay injected before capture), and
  writes the figure PNGs into `docs/user-guide/img/` named after the
  slots (planner.target, plan.save, plans.actions, …). **Constraint**:
  captures must run against a seeded demo dataset, never the dev
  deployment — screenshots are published-site material and the dev
  database carries live character and corporation names (the AGENTS.md
  rule). Refresh and expand the set at each milestone as surfaces
  stabilize.
- **Plan-of-Plans overview** (owner note, M6 schema review 2026-11-24):
  a single overview aligning all rostered characters and job
  requirements across every existing plan — a Gantt-chart style of
  upcoming jobs, pre-aligned to the plans the M6 one-claim job
  correlation has pinned jobs to (a job installs against one plan
  only, so the overview reads the pins, never re-matches). Future
  milestone investigation — M9's scheduling surfaces and M11's DAG
  visualization are the natural homes. **The stacking scenario of
  record** (owner note, M6 export review 2026-11-24): repeated
  deliveries of the same build on a cadence — e.g. the same weekly
  deliverable planned four times over a one-month horizon, four linear
  iterations of one chain — plus the copy workflow it composes with
  (same build re-planned from a different container input/output
  location in the corp hangars; Copy plan is that workflow's front
  door). Linear stacking of copied plans is the v1 shape; deeper
  dependency between the iterations is M9+ material.
- **Planner UI a11y (accessibility; from mockup iteration, 2026-11-18)** — rides
  M4's planner-entry implementation (2026-11-22 fold-in note): the Purchase ⇄
  Build chip is a `cursor: pointer` span in the wireframes but must ship as
  a `<button>`; the blueprint-search autocomplete rows need keyboard
  navigation (arrow keys + enter, focus management).
- **Session persistence for region/category filters** — the character
  selection is remembered across page visits (see
  `character_filter_groups` / the `?chars=` sentinels); extend the same
  treatment to the region and category dropdowns if it feels inconsistent
  in use.
- **Assets-page re-auth deep links** — anywhere the UI sends users to
  re-authorize, pass a `?next=` destination (the mechanism exists:
  `VALID_NEXT` in `app/routes/auth.py`) so they land back where they
  started.
- **Paused skill queues on the roster** read "Paused"; an entirely empty
  queue still reads "—" — revisit wording if it confuses.
- **Corporation filter on the Character Roster** — show the corporations
  (with corp icons) as a selector across the top of the roster; selecting
  one or more filters the character cards to those corps. Possibly also
  group the cards into per-corporation sections instead of filtering —
  the two approaches could be combined (sections + a filter that hides
  whole sections). Approach TBD; investigate later. Corp data is already
  in place (`characters.corporation_id`, `universe_corporations` for
  names, and the assets page's corp-row picker in `corp-rows.js` is a
  UI precedent worth reusing).
