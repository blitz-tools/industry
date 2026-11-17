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
- **ESI client**: ETag-cached GETs with per-character token refresh
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

### Documentation site (mkdocs + GitHub Pages)

A documentation site published via GitHub Pages, sourced from a `/docs`
folder in the repo. README.md stays a clean, concise overview that links
to the site.

- **Tooling**: mkdocs (material theme if it earns its weight), a GitHub
  Actions workflow deploying on pushes to `main` via
  `actions/deploy-pages` — same review flow as code changes.
- **Sections**:
  - *Installation & setup* — clone, `.env`, EVE SSO application
    registration (callback URL, scope list), container startup, first
    login, SDE import (`python -m app.sde import`).
  - *Development process* — the containerized workflow: podman compose,
    tests/lint/migrations in-container, the `.dev-reload-paused` marker,
    branch → PR → CI → merge with product-owner review.
  - *User guide* — characters and re-auth, roster, asset browsing
    (filters, structure panels), the Corporation section (main
    character, role gate, assets/blueprints/jobs pages), and the
    planner as it lands (M4+).
- Keep pages near the code they document and update them alongside
  milestone work so they drift slowly.

---

## Industry planner track

Large, sequential: structure manager → planner → build plans.

### Structure manager

User-managed registry of structures with the metadata the planner needs —
where industry happens changes materials, time, and cost, so calculations
must be per-facility. Input form (per structure):

- **Activity**: Manufacturing, Invention, Reactions
- **Structure name** (free text, display)
- **Structure type**: NPC station, Raitaru (small), Azbel (medium),
  Sotiyo (x-large) — available types depend on the selected Activity
  - Domain note: engineering complexes (Raitaru/Azbel/Sotiyo) cover
    manufacturing/invention/copying; reactions use refineries (Athanor
    medium, Tatara large) — include those when Activity = Reactions.
- **Material Efficiency rig**: No rig, T1, T2
- **Time Efficiency rig**: No rig, T1, T2 (reactions use reaction rigs)
- **System security**: High, Low, Null (rig effectiveness scales with
  security — confirm exact multipliers from CCP structure docs when
  implementing)
- **Solar system** (optional; type-ahead lookup against
  `universe_locations`/ESI — feeds the system cost index lookup)
- **Tax rate** (percent)
- **Default for activity** checkbox (one default per Activity — the
  planner pre-selects it)

Context: `UniverseLocation` already stores player structures seen in
asset sync (`kind="structure"`, `system_id`, `region_id`); this is a new
user-facing table on top, not a change to sync. A new "Structures" admin
page with CRUD. System cost indices come from public
`/industry/systems/` (cacheable like other universe data).

### Industry planner

Search and select a blueprint, then calculate a build plan:

- **Blueprint inputs**: number of runs, blueprint ME/TE. Owned
  blueprints for characters and the corporation are already synced
  into the owner-keyed `blueprints` table (ME/TE/runs; originals run
  -1) — the planner reads them, no ESI involved.
- **Character skills**: Industry and Advanced Industry levels (0–5),
  already synced into `skills` per character. The table stores trained
  and active level separately (active includes implants/boosters);
  pick deliberately per use — slot ceilings and requirements check
  trained level, time math arguably wants active.
- **Facility**: structure + rigs from the structure manager (default
  per activity, overridable), tax rate, and the system's cost index.
- **Market price comparison**: build-vs-buy decisions for materials,
  components, and reactions, plus profitability of the product itself.
  Price data from public market endpoints (`/markets/{region_id}/orders/`,
  `/markets/{region_id}/history/`, `/markets/prices/`) — needs a cached
  price pipeline and a region selector.
- Output: materials required (adjusted for ME/rigs/facility), production
  time, installed cost, and buy-vs-build guidance per input.

### Build plans (planner follow-on)

Export a build plan from the planner; load and track it under a "Build
Plans" (and eventually "Corporate Build Plans") menu item. Shows progress
towards gathering required inputs (materials, components, reactions…)
measured against character and/or corporation assets — the assets tables
and per-type aggregation (`structure_page` in `app/assets.py`) already
provide the availability side. Industry jobs for both sides (characters
and corporation, completed history included) are already synced into
`industry_jobs`, so correlating installed jobs to plan nodes is a join.

---

## Platform / administration

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

---

## Smaller items / ideas

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
