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

*(Documentation site landed 2026-11-17: mkdocs-material under `docs/`,
deployed to GitHub Pages by the `Docs` workflow; README links to the
site. Keep pages near the code they document and update them alongside
milestone work so they drift slowly.)*

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
`/industry/systems/` (cacheable like other universe data; the sync
itself lives in M15's world-state band).

### Industry planner

Search and select a blueprint, then calculate a build plan:

- **Blueprint inputs**: number of runs, blueprint ME/TE (Material/Time Efficiency). Owned
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
  `/markets/{region_id}/history/`, `/markets/prices/`) — all of it syncs
  in M15's world-state band (region policy decided 2026-11-19: five NPC
  hub regions plus custom hubs, The Forge default, plan-time selector);
  M10 is the analysis over those local tables.
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

**Plan home and lifecycle** (product direction, 2026-11-22): the
calculated active build plans live under **Corporation → Jobs** —
review, tracking, and management from one place, with management
meaning **delete**, and **copy for re-use after completion** (a
finished plan becomes a template: same target and pool, re-measured
against current stock). Refinement needed at implementation: the
current Corporation → Jobs page shows *synced industry jobs* (the
ESI mirror), so decide how plans surface there — alongside the raw
jobs, or as a plans view with correlated jobs nested under it.

**Multibuy export** (product direction, 2026-11-22): the build-plan
page exports its shopping list — raw-material gaps plus the
components/commodities flipped to Purchase ("components-to-buy") —
in the **standard EVE multibuy format**, one line per item:

```text
Item Name<TAB>Quantity
```

e.g. `Tritanium    50000` — item name, a literal tab, the quantity.
Pastes straight into the in-game multibuy window and market quick
buy. The header's export button (⭳) is the natural trigger; scope
per plan with the same pool/market selections as the page. Buy
verdicts from the Market panel feed the components-to-buy set.

**Plan-scoped material buckets via station containers**
(investigated 2026-11-20 — feasible):

- The goal: run multiple concurrent build plans without
  cross-contaminating the availability math — each plan's input and
  output materials live in their own named station container, so a
  plan measures a plan-scoped pool instead of the shared hangar.
- **Feasibility confirmed against live data (2026-11-20)**: station
  containers and their contents already sync through the existing
  assets machinery — no resolver or sync changes needed. Contents are
  ordinary asset rows with `location_id` = the container's `item_id`,
  `location_type='item'`, `location_flag='Unlocked'`, and
  `parent_location_id` already resolved through the container's own
  location row (the asset-snapshot hop handles the nesting). Verified
  on the live roster: 14 character-owned Station Containers (8 with
  contents — e.g. one holding 113 distinct types — 6 empty), plus
  Giant Secure and Huge Freight containers. None sit in corp hangars
  today; placement there is a practice step, not a code step (the corp
  asset sync is identical, owner-parameterized machinery).
- The pool-scoping primitive is one join: plan → its container
  `item_id`s → `assets WHERE location_id IN (…)`. Availability meters,
  acquisition gaps, and delivered-output tracking all filter through
  it; the shared hangar stays available as the fallback pool.
- **Container names DO come from ESI** (corrected 2026-11-20 after
  live verification): `POST /characters/{id}/assets/names/` (and the
  corporation variant) returns custom item names for arbitrary item
  ids, under the already-registered `esi-assets.read_assets.v1`
  scope — no portal change needed. Live-tested against the roster's
  containers: 8 of 9 returned their in-game names (`'|____ manu.
  output'`, `'__charges'`, `'__damaged crystals'`, `'[drones]'`,
  `'__loki'`, `'__fuel blocks / minerals'` … — the roster already
  organizes builds this way). **Gotcha**: a batch containing any id
  that was never custom-named fails wholesale with
  `404 {"error":"Invalid IDs in the request"}` — the sync must
  filter or retry around invalid ids per-item. Names are free text
  (one container is literally named `None`). The names pass belongs
  in the asset sync (cacheable like the rest).
- **Workflow investigation still open (product owner, 2026-11-20)**:
  how to identify a container in-game and link it to its app-side
  plan entry in a human-consumable way — e.g. a naming convention
  where containers are named in-game for a particular build ("PLAN —
  jackdaw ×1") so it's clear which `item_id` belongs to which build.
  With names syncing (above), the app can surface each container's
  in-game name and contents to disambiguate at binding time, and the
  plan can suggest its own container name to copy in-game.
- **Unverified pins (check at M6 pickup)**: (a) whether industry
  installs can consume materials and/or select blueprints directly
  from container contents — if not, bucketing is a staging layer and
  the plan should model the explicit "dump container → hangar at
  install" move (job output always delivers to the installing hangar,
  so output bucketing needs the reverse move too); (b) ESI's behavior
  for locked/passworded audit-log containers (every live sample is
  Unlocked — Station Containers are in the 'Audit Log Secure
  Container' group).

### LP stores & faction BPCs — data layer + acquisition mechanic

(recorded 2026-11-21, per product direction; feeds the planned
faction-components mockup set — design/README.md list item 6)

**The mechanic**: faction commodities' BPCs are purchasable only
from **LP stores** — faction modules, launchers, and
faction-equivalent hulls (e.g. the Typhoon Fleet Issue's BPC comes
from an LP store, not invention). **Note (corrected 2026-11-21 after product-owner review): the
faction-ammo world splits** — Republic Fleet **Carbonized Lead**
and **Depleted Uranium** (S/M/L/XL) ARE buildable: LP-store BPCs,
producer-less in the SDE, maxPL 200, **100 rounds per run**,
trivial mineral bills, Industry 1 (the volume faction commodity).
The damage-typed variants (Republic Fleet EMP / Fusion / Phased
Plasma, Caldari Navy missiles) have no blueprint types — LP-store
**finished goods**, buy-vs-build targets at the commodity level. LP (Loyalty Points) is a separate, faction-typed
currency earned through missions, faction warfare, and similar;
there is no in-game market for LP itself, but characters can
transfer LP among each other. LP is spendable only at the matching
faction's LP store, located in NPC stations, and the store's
offering list determines what is purchasable. This is the **fifth
blueprint acquisition path** (invented · contracted · NPC-seeded ·
drop-sourced · LP-earned).

**Findings against current data (2026-11-21, updated same day)**:

- The SDE mirror has **no LP tables** — LP store offers (LP cost +
  ISK + required items per offer) are not in the fuzzwork dump
  (the mirror is verbatim, so the dump lacks them). The acquisition
  catalog needs a new source: candidates to evaluate at pickup are
  the official SDE YAML exports (check for lpstore tables on the
  next release review), community datasets (e.g. EVE Ref), or
  curated pin tables verified in-game by the owner.
- **Loyalty scope registered 2026-11-21**
  (`esi-characters.read_loyalty.v1`) — character LP via
  `/characters/{id}/loyalty/points/` (per-faction balances) is
  live-probed as an existing route; balances sync once characters
  re-auth. Also registered for future efforts:
  `esi-contracts.read_character_contracts.v1` and
  `esi-contracts.read_corporation_contracts.v1` (the
  contract-match fallbacks and contract-acquired BPCs — Hel-BPC
  style).
- **Corporation LP has no ESI route** (live-probed 2026-11-21):
  `/corporations/{id}/loyalty/points/` 404s at every plausible
  path — there is no corp read_loyalty scope, matching the portal.
  Corp LP is real in-game (the FW militia mechanic — blitz and
  blitz holdings holds it, consistent with Amamake being the
  Minmatar militia home) but **not syncable**: the app models it
  as either a curated manual balance (structure-manager-style
  user-maintained entry) or the in-game distribution path —
  directors withdraw corp LP to characters, at which point it
  becomes character LP and syncs. Adjacent ESI surface that DOES
  exist: `/corporations/{id}/fw/stats/` and
  `/characters/{id}/fw/stats/` (kills / victory points, not
  balances — scope registration needed if used).
- Faction BPs are **BPC-only**: the Typhoon Fleet Issue Blueprint
  (32312, maxPL 10) has no producer anywhere in the SDE — build
  side fully covered by the chain walk, acquisition side entirely
  LP-shaped.
- The LP-transfer-between-characters mechanic (wallet-like
  balances, not a market commodity) still needs modeling.

**Offer catalog source FOUND (2026-11-21)**: fuzzwork's lpstore
tool publishes the full LP store database —
`fuzzwork.co.uk/lpstore/data/lpOffers.csv` (offerID,
corporationID, typeID, quantity, lpCost, akCost, iskCost) +
`lpOfferRequirements.csv` (offerID, typeID, quantity) — **31,952
offers across 181 store corporations, 452 distinct BPC types**,
plus a JSON API (hourly cache). This slots into M15's world-state
family set (public, cacheable, CCP-data-derived). Live-verified
against the Typhoon Fleet Issue Blueprint: four offer variants at
the **Tribal Liberation Force** (1000182, the Minmatar FW militia
corp — not the navy): 100k LP + 0 ISK + 2× Minmatar UUC Nexus
Chip · 100k LP + 20M ISK clean · 100k LP + Hakim Stormare's Tag ·
**200k LP + 200M ISK for a 10-pack** (20k LP + 20M ISK per BPC —
the variant choice is a real planning decision). Navy stores
(Republic Fleet et al.) sell the same BPCs at 500–600k LP — the
militia store is ~5× cheaper, which makes FW LP the efficient
path and ties the set to the militia world. Pin: the RF
Carbonized Lead / Depleted Uranium ammo BPCs (SDE-buildable) have
**no offers in the fuzzwork dataset** — verify in-game which
store sells them before relying on the catalog for ammo.

**Corporation LP acquisition (investigated 2026-11-21)**: no ESI
route exists (probed; the FW stats route
`/corporations/{id}/fw/stats/` exists but carries stats, not
balances — scope `esi-corporations.read_fw_stats.v1` pinned from
its 401). The corp's LP is **militia corporation LP** (TLF —
consistent with Amamake and the cheap militia BPC pricing), held
on the corporation and visible only in-game. Two modeling paths,
both to support: (a) **curated manual balance** — a
structure-manager-style user-maintained entry per corporation,
owner-verified against the in-game wallet; (b) **the in-game
distribution workflow** — directors withdraw corp LP to
characters, converting it to character LP at the same corporation
(where it syncs and the store is unchanged — corp TLF LP
distributed to a character spends at the TLF store identically).
The plan surface should show both: the curated corp balance as a
pool, and the distribution step as a plan item when the pool is
the source.

**Shortfall detection (computable end-to-end once synced)**: the
loyalty read returns balances keyed by `corporation_id` — the
same key as the offer catalog's store corporations — so
offer-cost vs held-LP per corporation is a direct join, including
the live gap story: the roster's TLF character balances are all
zero and Republic Fleet only 8.5k, against the TFI BPC's
100k–200k LP militia price — the earn-side lead time is the
plan's front story. The Paragon wealth (~632k LP) is
wrong-currency: LP does not convert between corporations.

**Design surfaces the set will need**: LP balances per character
per corporation (wallet-style) + the curated corp pool, the
corporation-matching constraint (store ↔ LP corporation), offer
browsing (what BPCs cost in LP + ISK + items, with variant
comparison), and the acquisition plan node ("earn or transfer N
LP, then purchase the BPC") — including the earn-side lead time,
which is gameplay (missions/FW), not industry.

### M5 expander: test harness + whole-catalog census (future, may-build)

(recorded 2026-11-21, per product direction — build at M5, not before)

The production expander M5 builds is a separate implementation from
`reference/chain_expand.py` (the executable spec), with the recorded
upgrades: terminator classification via the SDE's own group data —
a static group→category mapping (most groups map cleanly:
'Salvaged Materials', 'Harvestable Cloud', 'Mineral', …) with a
small name-list fallback for the known exceptions ('Commodities'
catch-all tools, Morphite misfiled under Mineral, producer-less NPC
goods — no group signature) — plus cycle detection and
multi-producer disambiguation (84 types, mostly faction variants).
New items in known groups classify without code changes.

Two validation tools we may want at that point:

1. **Reference-chain test harness** — run the M5 resolver against
   each recorded chain's (target, quantity) and diff its outputs
   against the known-good reference. Comparison target should be
   `chain_expand.py`'s structured output rather than the chain
   documents' markdown tables (parsing those is fragile): likely a
   `--json` mode on the reference script, or a harness that invokes
   both implementations and diffs the trees, phase tables, raw
   totals, and invention layers. The eight chains (Typhoon, Charon,
   Panther, Jackdaw, Trimark, Rage, Crash, + supercarrier/titan when
   they land) are the acceptance suite; a faithful M5 port
   reproduces every one.
2. **`--all` whole-catalog census** — expand all ~5,014 buildable
   products once and report the failure classes: cycles found,
   unclassified terminators reachable, multi-producer types,
   walk failures. Run as an SDE-release regression (the game adds
   items at every release point): a clean census proves the
   resolver is total; findings are the implementation gaps to
   close. The 2026-11-20 census numbers are the baseline — 84
   multi-producers, 0 multi-product reactions, 5,014 buildable
   products.

### Contract matches in acquisition fallbacks

(surfaced by `design/panther/planner-scoped.html`'s Fallback section,
2026-11-20)

- The unresolvable-path fallbacks ("no eligible character" gating,
  missing-blueprint contract acquisition) currently bottom out at
  "watch the contracts for a listing and re-calculate when one
  appears" — a dead end with no evidence. Once M15's contracts sync
  is live, these sections should list **matching contracts**:
  every listing that satisfies the requirement (item-exchange
  contracts whose items match the needed blueprint/commodity), each
  with its **contract price**, so the owner can see at a glance
  whether any exist and what they cost.
- Mechanics already decided (M15 + the Charon/Panther contract
  work): per-region listing + items sweep into `contracts` /
  `contract_items`, ETag-cached, hub regions; exclusive-contents
  matching and the item-exchange + volume-band pre-filter exist from
  the missing-blueprint decisions. The fallback list is a query over
  those local tables — same-bundle matching (the Charon's
  same-type-bundle corner) and tight-volume single-item matches
  first.
- Empty state stays honest: "no listings in the synced hub set" with
  the sync-source line, never an error.

### Skill-plan calculator for participant gaps

(surfaced by `design/panther/planner-scoped.html`'s Plan participants
section, 2026-11-20)

- The participants section surfaces the state where the
  default-included corp members **lack the skill set to create the
  commodity** (the scoped Panther: no corp member holds the
  invention skills). Today the remediation is manual — include an
  out-of-corp holder, or train someone by hand.
- Future feature: a button on that state that **calculates a skill
  plan across the characters** identifying the fastest path to
  satisfying the requirement's skill set — training time per skill
  per character (from the synced skill queues and skill points),
  prerequisites included, and crucially **splitting skills across
  characters** so requirements are satisfied sooner (two characters
  each training half the gate list in parallel beats one training
  all of it, exactly like job parallelism).
- Shape: the same chain-tree treatment the product planner gives
  materials — a dependency tree over skills (prerequisites), a
  parallelism analysis across characters' training queues, and a
  recommended assignment with end dates. Extends M13 (skill gap
  analysis & training recommendations — see MILESTONES.md) from
  single-character recs to a **multi-character fastest-path
  optimizer**; the plan-time gate that surfaces the state is
  recorded in MILESTONES ("unresolvable paths force an acquisition
  fallback").
- **Generalization — a Skill Planner surface** (product direction,
  2026-11-22): the calculator's logic stands alone as a planner in
  its own right, mirroring the build planner's shape — pick a
  target commodity and the characters available, and it produces a
  **skill queue across characters** with the same balancing the
  industry side does (parallelism across characters, requirements
  split for earliest satisfaction) rather than a single-character
  training list. Decide at design time how much surface it shares
  with the build planner (target picker, participants section) —
  the mechanics overlap enough that it may be a mode of the planner
  rather than a separate page.

### Plan-assignment eligibility for out-of-corp characters

(surfaced by the Plan participants mockup work, 2026-11-20)

- The planner's **Plan participants** section offers any rostered
  character for per-plan inclusion. The implicit assumption: every
  rostered character belongs to the application owner, so all are in
  scope for assignment — true today (the roster is the owner's own
  accounts across three corporations: blitz and blitz holdings,
  chlorokitties, The Dark Tribe).
- **Missing**: a configuration determining which out-of-corp
  characters are *valid* for inclusion at all — a per-character
  "available for plan assignment" eligibility flag. Candidate
  surface: the **Roster screen** (a per-card toggle alongside
  `is_main`). Corp members could carry the same flag (default on) so
  an inactive member is excluded roster-wide rather than per plan.
- The **corp-member vs other-corporations segregation stays**
  regardless of the flag: out-of-corp characters have no hangar
  access, so their work requires the distribution step (contract /
  station trade) to export inputs and import outputs back to the corp
  hangars — a separate set of in-game procedures the plan already
  models as the per-plan inclusion cost.
- Interactions when built: the participants section's Include
  controls offer only eligibility-flagged characters; the capability
  analysis (M12) and capsuleer bidding (M14) consume the same
  eligible set.

---

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

### Navbar refinement — item inventory

(surfaced by the M3 structures mockup, 2026-11-22)

- **Structures sits top-level, under Build Planner** — the registry is
  planner-adjacent user state (every calculation multiplies against
  it), not administration; the mockup nav places it there and the app
  nav should follow at M3.
- A deliberate pass is needed to **identify the remaining navbar
  items** as surfaces land. Known so far:
  - **Character → Roster** — the main-character set and participant
    pool source (the planner's participants section and the
    corporation scoping both read from it).
  - **Corporation → Jobs** — grows into the planner's plan home
    (review, tracking, management; see the Build plans section's
    lifecycle note above).
- The mockup sidebar across `design/` should follow whatever this
  pass lands — the chain sets predate it and still show the older
  nav.

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

- **Planner UI a11y (accessibility; from mockup iteration, 2026-11-18)** — when the
  `design/typhoon/` components ship in the app: the Purchase ⇄ Build chip
  is a `cursor: pointer` span in the wireframes but must ship as a
  `<button>`; the blueprint-search autocomplete rows need keyboard
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
