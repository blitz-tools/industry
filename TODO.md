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

- **Personal-stock coverage toggle** (owner note, M5 review 2026-11-24):
  the planner's coverage measurement defaults to the corp office
  hangars (`chain_plan(include_personal_stock=...)` opts into
  participants' personal hangars — the false-positive guard for
  out-of-corp job-allocation participants). No planner-input control
  exists for it yet: mock up where the toggle lives (the Plan
  participants section is the natural home, next to the pool it
  measures) and implement it as a URL-state param following the
  absence-means-default convention.
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
  other open-source observability applications.
- **Code tracing for future debugging** (future work): implement
  via **OpenTelemetry (OTEL)** where possible — request/job spans
  extending the metrics conventions M15 already records (zero-code
  Python instrumentation; the uv bootstrap caveat is documented in
  MILESTONES.md's M15 note).

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
