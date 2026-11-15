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
  + corporation variants of assets, blueprints, industry jobs, market
  orders, wallets, projects, skills, skill queue, location.
- **Assets page purity rule**: page renders never touch ESI; everything
  resolves through the background sync into DB tables first.
- **UI patterns to reuse**: collapsible rows/cards with sync-state rings
  (assets toolbar), notification boxes (`CardIssue`), in-place content
  swaps (`swapAssetsPage` in `app/static/app.js`), remembered open/closed
  state via localStorage (`corp-rows.js`).

---

## In queue

### Main character selector (prerequisite for the Corporation section)

A selectable "main" character determines which corporation the Corporation
section manages. The main must hold Director or CEO in that corp; their
tokens authorize the corp-scoped ESI calls. All characters can be added,
but they are not necessarily in the same corporation — the Corporation
section targets exactly one corp (the main's).

- `Character.is_main` (single-user app today, one flag suffices) with a
  "Set as main" action on the roster cards and a "Main" badge.
- Corp resolution from the main's public `/characters/{id}/` data
  (`corporation_id` — already fetched and persisted on roster renders).
- Role enforcement: check `/characters/{main_id}/roles/` before syncing
  corp endpoints. **Prerequisite: register the
  `esi-characters.read_corporation_roles.v1` scope on the portal** — it is
  not in the current set. Director/CEO → proceed; otherwise show an
  explanatory state instead of burning the error budget on 403s (same
  philosophy as restricted-structure parking).
- Switching mains switches the targeted corp snapshot; old corp data can
  stay in the DB, just untargeted.

Follow-on (same track): **corporation assets** — corp assets/jobs/wallets/
blueprints endpoints return the same shapes as their character
counterparts; the sync and view layers are already owner-agnostic.

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

- **Blueprint inputs**: number of runs, blueprint ME/TE. Character and
  corporation blueprints are already reachable — scope
  `esi-characters.read_blueprints.v1` is registered; the endpoint returns
  type_id, ME/TE, runs, location.
- **Character skills**: Industry and Advanced Industry levels (0–5) —
  `/characters/{id}/skills/`, scope `esi-skills.read_skills.v1`
  registered.
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
provide the availability side.

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

- **CI: upgrade actions off deprecated Node.js 20** — GitHub is
  deprecating Node 20 on Actions runners
  (github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners);
  `actions/checkout@v4` and `astral-sh/setup-uv@v5` in
  `.github/workflows/ci.yml` currently trigger the forced-Node-24
  warning. Bump both to their current major versions (checkout v5+,
  setup-uv v6+) and re-run the workflow to confirm the warning clears.
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
