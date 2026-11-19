# Milestones — Industry Planner

The build-out plan for the industry planner, derived from `TODO.md` (which
stays the surface for small items and ideas). Each milestone carries its
goal, scope, and a validation step, so a session can pick one up and go.
Order matters within a track, not across all of them — dependencies are
called out explicitly.

Validation case throughout: the **Typhoon** (T1 battleship) blueprint. The
chain it produces (ship → components → reaction intermediates → moon
materials, PI (Planetary Industry) commodities, and minerals) is familiar ground and
exercises phases, blueprint availability, and asset measurement.
Correction (2026-11-16, confirmed against the live mirror): the chain
**does require reactions** (though not invention) — the components take
reaction products (Pressurized Oxidizers, Reinforced Carbon Fiber)
whose own recipes are a further reaction layer consuming fuel blocks
(manufacturing) and moon materials. Reactions commonly sit in the
early, deep portions of even T1 chains, which is why reaction
resolution is part of M5's initial scope rather than a later
extension. Invention arrives only with T2 targets; T3's interface
with it is to-be-determined (M8).

## End goal (clarified 2026-11-16)

A **work-distribution planner** for a single corporation and its
registered characters, building target products as efficiently as
possible — reduced material inputs with maximum time efficiency.

Input a target build and quantity; the system reverses the product
chain to raw-material inputs, then builds up every chain layer,
distributing the work across the corporation's characters based on
skill availability for each blueprint and chunking it across available
build slots so the components the next stage needs complete as fast as
possible. The parallelism mechanism is **BPC (Blueprint Copy) copies**:
the planner recommends how many copies to make from owned BPOs
(Blueprint Originals) and each one's run
count, so jobs install simultaneously across slots — a single
max-run job is always the most material-efficient but slowest, so
more slots are bought at a material cost. A **profit-vs-throughput
control** (plan-level, **three positions**, 2026-11-18) sets the
plan's posture: **profit** concentrates work on the builders and job
splits whose skills and run counts reduce input-material requirements
(most profit per build, everything in-corp); **balanced** farms chain
portions out to friends at below-market rates — the same wall-time
win as purchasing at lower cost; **throughput** purchases whatever
shortens wall time and fills every available slot to produce as many
final targets as possible in the shortest time.

The system closes the loop on the roster itself. Capability analysis
matches the corp's synced skills and owned blueprints against the
buildable catalog — recommending end products the corporation is
positioned to produce, and identifying per-target gaps (missing
skills, missing blueprints). Those gaps have three responses, which
is where the roadmap forks (equal-weight alternatives, owner's call
at pickup): **train** (per-character skill plans toward a target's
maximum efficiency), **farm out** (bid chain portions to friends as
paid contracts), or **pick a better target**.

---

## Status (updated 2026-11-16)

| Milestone | State |
|---|---|
| M1 — main character & corporation pool | ✅ **Complete** (PRs #12–#14) |
| M2 — SDE (Static Data Export) foundation & blueprint catalog | 🟡 **In progress** — SDE foundation + admin self-update (PRs #15–#16) and the character-side data syncs (PR #17) complete; remaining: catalog surface |
| M3+ | Not started |

**Pick up at**: M2 remainder — the catalog query layer the M4 planner
consumes (blueprint search, recipe joins, owned-blueprint overlay; the
SDE-name vs `universe_types` merge rule gets decided there). Everything
below M3's heading is still plan; the landed sections record where
reality diverged.

Live anchors for a fresh session: schlepzrage is the main (Director,
corp 98830898, all corp data synced); SDE release 2026-11-13 mirrored
(53,925 types) and self-maintaining; the Typhoon recipe reads end to
end through the mirror (blueprint **998** → ship **644**, three
buildable components, Industry 1, 5.0h base). All eight characters
sync blueprints, skills, and jobs (char + corp sides both live: 754
character blueprints, 1,099 skills, 44 character jobs), so the
owned-blueprint overlay and skill math have real data to join against.
Two things worth knowing before the catalog work: the skills table
carries **trained vs active** level separately (active includes
implants/boosters — M4's time math should pick deliberately), and
`UniverseResolver.resolve_location_ids` is the ready-made primitive
for naming any location id that arrives without a type (the M6 jobs
correlation and any future Location column want it).

---

## Architecture: three data layers

Every planner feature is a join across exactly these layers. Keeping the
split crisp is what lets T2/T3 and reactions arrive later as *data and
resolver extensions* instead of schema rewrites.

| Layer | Source | Nature | Examples |
|---|---|---|---|
| **Static (recipes)** | EVE SDE, imported | Write-once per EVE release | blueprint → materials, products, required skills, activity durations, invention probabilities |
| **Dynamic (world state)** | ESI (EVE Swagger Interface), ETag-cached sync | Refreshed in background | owned blueprints (ME (Material Efficiency)/TE (Time Efficiency)/runs), skills, industry jobs, assets, cost indices, public contracts, market prices & regional orders/history (M15) |
| **User state** | This app | User-managed CRUD | main character, structures, build plans, job assignments |

Two consequences worth stating outright:

- **ESI cannot answer "what does this blueprint build from."** The
  production chain lives in the SDE (`industryBlueprints` as the
  registry, `industryActivityMaterials`, `industryActivityProducts`,
  `industryActivitySkills`). ESI supplies what the SDE can't: which
  blueprints you own, who you are (skills), what's installed (jobs),
  where things sit (assets), and what it costs (indices, later prices).
- **The schema models all industry activities from day one** —
  manufacturing, copying, invention, reactions, and T3 reverse
  engineering — via a generic activity dimension. V1 *resolves* the
  T1 manufacturing + reaction chain (reactions included per the
  revised v1-scope decision); invention/T2 and T3 land incrementally
  without migrations that retrofit activity types.

### Decisions already made

- **SDE source**: managed import command — downloads the fuzzwork SQLite
  dump for the current EVE release and mirrors it verbatim (see M2's
  landed-as notes). Re-run per release; nothing checked into git.
  Landed 2026-11-16 with the admin self-update.
- **V1 chain scope** (revised 2026-11-16): T1 manufacturing **and
  reactions** — even the Typhoon validation chain carries two reaction
  layers, so reactions resolve with the initial chain (M5) rather than
  as a later extension; invention/T2 and T3 follow. Schema supports
  all from the start.
- **Market pricing**: deferred (separate milestone, near the end). The
  planner computes materials, time, and install cost from tax + system
  cost index; build-vs-buy and profitability come with the market
  pipeline.
- **Visualization**: phase-grouped expandable views first (reusing the
  assets-page collapsible-row patterns); interactive node-graph DAG is
  its own follow-up milestone.
- **Reference implementation** (2026-11-17): proof-out scripts in
  `reference/` — chain expansion (M5), the time-balanced
  scheduling/timeline model with per-character skill multipliers
  (M4/M9), and BPO obtainment recommendations (M12) — regenerate
  `reference/chains/TYPHOON-CHAIN.md`'s golden values and are the executable spec the
  milestones graduate into the app. See `reference/README.md` for the
  formula reference and flagged assumptions.
- **Stage-state model** (2026-11-18, from the mockup iteration —
  `design/typhoon/` is the visual spec): five node states — Missing
  inputs, Ready to build, In progress, Ready to deliver, Stage complete
  ("In progress" fills the spec's gap between Ready to build and Ready
  to deliver) — carried by the state chip, with the gating reason (BPC
  copy progress, a waiting upstream phase) as secondary text + meter
  beside the chip. Phase summaries roll up from children (worst child
  wins); nodes marked Purchase drop out of the phase state and percent
  and count toward the acquisition side instead. Purchase ⇄ Build is
  node-level in the data model (purchase decisions are per-commodity)
  with a phase-level bulk toggle recovering stage-level ergonomics.
  Pre-calculation purchase intent is deliberately rejected
  (2026-11-18): the marking flow lives on the calculated plan — the
  same node-marking mechanism M14's farming reuses — so
  calculation-time inputs stay minimal.
  (M5/M6.)
- **Next-up assignment** (2026-11-18): each queued job is assigned to
  exactly one character — the spec's definite "the next job that should
  be executed in this slot" — and slot queues show the next job plus at
  most one "then", with a "+N more" count when the backlog runs deeper.
  (M9.)
- **Blueprint availability is plan-time** (2026-11-18): required-
  blueprint status (Missing / Owned) renders at build-plan time only;
  once a plan is active the blueprint set is considered immutable, so
  the active view omits the section. Purchasing removes the node's
  inputs from the raw-material math — the commodity itself is what
  gets acquired. **Missing-blueprint default (refined 2026-11-18,
  from the Charon chain)**: acquire BPCs off contract and backfill
  what the plan requires — owning a BPO for every component fails
  economy-of-scale (a fully-researched BPO costs isk; an unresearched
  one costs isk plus research time; BPCs cost far less but must be
  costed and availability-checked per plan, which needs contract /
  market data). Buying the commodity outright remains the alternative;
  BPC vs commodity vs BPO is an economy-of-scale call the isk math
  (M10) and the BPO-recommendation ladder (M12) inform. **Contract
  matching (2026-11-18)**: the availability check matches contracts
  whose contents are exactly the wanted item — a contract that merely
  includes the Charon BPC among other items is not a match, so the
  plan never prices unwanted bundled items. Whether same-type
  multiples (several identical BPCs in one contract) qualify is an
  implementation-time call. **Scan scope (2026-11-19, refined)**:
  contract searches default to the standard NPC trade-hub regions
  (The Forge, Domain, Heimatar, Metropolis, Sinq Laison) — where BPC
  contracts actually list. (The rollout is staged — The Forge first —
  per the market-data region policy.) Region stays display metadata on results,
  never a filter. ESI's public-contracts endpoint is per-region by
  construction and has **no item-level search** (the listing carries
  no contents), so candidates pre-filter on contract type
  `item_exchange` plus a tight volume band (a BPC contract is ~0.1
  m³) before the per-contract items call. **No price filtering** —
  below-market BPCs are finds, not noise. An all-region sweep
  remains possible but is not the default. **BPC selection
  bias (2026-11-18)**: when
  several contracts satisfy a missing blueprint, the
  profit-vs-throughput slider picks which — profit biases toward the
  highest ME (cost), throughput toward the highest TE (wall time),
  balanced toward the best combination (max on both ideally, else
  the highest average). Verified against live ESI: the public
  contract-items response carries `is_blueprint_copy`,
  `material_efficiency`, `time_efficiency`, and `runs` per BPC, so
  the bias needs no data source beyond the contracts sync.
  (M5/M6/M12; the sync itself is M15.)
- **World-state syncs land as one band** (2026-11-19): the remaining
  public-data sync families — cost indices, public contracts, global
  market prices, regional orders/history — implement together in M15
  as one cohesive set of functions and schema, rather than piecemeal
  across the milestones that consume them: one converged sync
  workflow, not the same pattern re-implemented per milestone. The
  framework decisions (a public-endpoint sync category with no scopes
  or role gates, per-family cadence and pruning, a shared rate-limit
  budget, one status view) are made deliberately once; schemas
  verbatim-mirror their payloads per the SDE lesson, so data lands
  statically and interpretation stays with the consuming query layer.
  Implementation does not imply consumption — each milestone reads
  the data when its surfaces need it, and the gap is a deliberate
  soak test: sync observability (status, rate limits, staleness) is
  pulled forward from the platform track to land with the band, and
  cadence/API-access tuning happens against real-world sync runs.
  Regional orders/history initially stayed with M10 (the parked
  region-choice question) and folded into the band the same day the
  market-data region policy resolved it — as the heaviest slice, with
  a staged rollout (The Forge alone first) so the soak test measures
  one region's headroom before coverage grows. Player-structure
  markets (the Amamake home structure's market module) ride along as
  the band's one character-scoped source, gated per the landed
  per-kind pattern. The landed character/corp syncs are not
  retrofitted onto the generalized framework. (M3/M10/M15.)
- **Market-data region policy** (2026-11-19): regional market data
  (orders, history, public contracts) syncs a user-managed hub set —
  the target default is the five NPC trade-hub regions (The Forge,
  Domain, Heimatar, Metropolis, Sinq Laison), one region-set concept
  across the world-state band, sharing its rate-limit budget. **The
  rollout is staged: the hub set starts with The Forge alone** —
  measure one region's rate-limit headroom before expanding
  coverage; a single region may already brush the limits. The set is
  **user-extensible in two directions**: additional public regions
  (custom region hubs, e.g. null-bloc markets), and
  **player-structure markets the roster can access** — the
  motivating case is the corp's own Amamake structure (5 Times Nearly
  Winners) with a market module. Structure markets sync through the
  character-scoped `/markets/structures/{structure_id}/` (a scoped
  sync kind riding the landed scope-gating pattern, not the public
  category); public contracts listed at that structure already arrive
  via the Metropolis region scan. Price lookups default to The Forge
  (Jita, the liquidity reference; M14's bid pricing already assumes
  it) with a plan-time selector among synced hubs — the corp builds
  and delivers in Amamake (Metropolis), so Jita-vs-local is a real
  per-plan choice. System-level hubs inside a synced region (Amamake
  itself) are a query-layer filter over that region's orders (the
  endpoint carries `system_id`), never extra sync scope. Full daily
  history is retained (append-only, one row per type per region per
  day); windowing is a query-layer concern, never a sync-shape
  decision. Region stays selection metadata on planner results, never
  a sync-scope change; an all-region sweep remains possible but is
  not the default. (M10/M15.)
- **Skill gate (2026-11-19)**: build planning checks each blueprint
  for usability as well as availability — at least one character in
  the pool holding the activity's required skills
  (`sde_activity_skills`: manufacture, react, invent). A blueprint
  with no skilled character forces its node to the purchase path
  (market or farming) regardless of BPC availability, and contract
  searches for it are skipped as unnecessary. The calculated plan
  marks these nodes distinctly — skill-gated, not blueprint-gated —
  so the acquisition story explains why purchase is forced.
  (M4/M5/M9; eligibility was already M9's assignment input — this
  makes it a plan-time gate. Live check 2026-11-19: the roster passes
  the Charon chain — Octavia holds Capital Ship Construction.)
  **Waves and job alignment respect the same eligibility (2026-11-19)**:
  a wave's install requests only go to characters holding the job's
  required skills, and single-holder skills serialize that work onto
  one character regardless of free slots — the wave view makes the
  bottleneck visible (e.g. every Capital-Ship-Construction job in a
  Charon plan lands on Octavia alone). **Plan calculations weight
  durations by assignee (2026-11-19)**: job alignment feeds the time
  model — each job's duration uses its assigned character's skill
  multiplier, so who runs what changes the chain-end estimate. The
  scheduler assigns eligibility-first, then optimizes: the
  throughput end puts jobs on the fastest eligible characters, the
  efficiency end runs the skill-weighted distribution; single-holder
  skills serialize both the jobs and the multiplier. The reference
  model's single-multiplier runs remain scenarios, not the app's
  behavior.
- **Planner requirement overview** (2026-11-19): pre-calculation shows
  the full per-unit chain in three collapsible tiers — blueprints
  (owned/missing status with a contract-backfill peek on missing),
  intermediates (grouped by phase, per-unit quantities), raw
  terminators (by category, with coverage standouts) — quantities
  tracking the target stepper live. Calculate schedules (phases,
  waves, allocation, copy plan); the chain itself resolves at
  selection. Direct-inputs-only was rejected: it is
  recipe-dependent-inconsistent (the Typhoon takes minerals directly,
  the Charon takes none). The tier list is open-ended — invention
  inputs join as their own tier when M8 chains arrive, kept simple at
  the overview level: the source-BPC → invented-BPC relationship
  (Typhoon BPC → Panther BPC) and nothing more. The rich invention
  math — decryptor selection, success rate per decryptor, decryptor
  inventory vs purchase — lands on the calculated plan (M8 pickup).
  (M4.)
- **Phase numbering** (2026-11-18): phases count up in build order —
  raw-material terminators at phase 0, a node's phase = 1 + max(its
  inputs' phases), target at the highest number — so phase and wave
  numbers both increase toward completion (waves are temporal install
  batches, phases are dependency layers; progress moves both counters
  the same direction). The mockups, the reference scripts, and
  `reference/chains/TYPHOON-CHAIN.md` all use the ascending
  convention (the reference renumber landed 2026-11-18 alongside the
  first new chain document). (M5.)
- **Copy-vs-direct presentation** (2026-11-18): the planner applies the
  copy-vs-direct rule (`reference/chains/TYPHOON-CHAIN.md`) in its
  wave composition but does not surface the calculation as dedicated
  UI — the wave job
  requests are the surface: an early wave requests the blueprint copies
  later phases need, and a later wave's job request simply uses the BPO
  directly where a copy was unnecessary. (M9.)
- **Purchase-vs-copy crossover** (2026-11-18, from the ×10 simulation):
  purchasing a node (or phase) wins on wall time whenever procurement
  lead time < the node's copy-queue overflow + build time. For the
  Typhoon chain the AIPS (Auto-Integrity Preservation Seal) copy
  queue ÷ reaction dead zone = 1.56 at
  every target count, so the copy pipeline is the constraint at any N
  — there is no scale at which copying catches up, and purchasing
  phase 4 collapses phases 1–3 out of the math entirely (their
  outputs lose their only consumers). The time side is closed-form;
  whether to pay is the slider's job (the isk side needs M10). The
  waves carry the outcome — no dedicated UI, per the copy-vs-direct
  presentation decision above.
- **Slider is three positions, not a continuous bias** (2026-11-18):
  **profit** (left — build in-corp at maximum efficiency), **balanced**
  (middle — farming: farm chain portions to friends at below-market
  rates; the same wall-time win as purchasing at lower cost), and
  **throughput** (right — purchase whatever shortens wall time). Three
  discrete plan postures; supersedes the two-ended continuous-slider
  wording in the end goal and M9. (M9/M14.)

---

## M1 — Main character & corporation pool — ✅ COMPLETE (PRs #12–#14, 2026-11-15/16)

*Landed as planned, plus more: the corp blueprints and industry jobs
syncs originally sketched for M2 landed here (PR #14), and the
structures scope arrived early (see below).*

**Landed as**

- `Character.is_main` (migration 0006), roster "Set as main" (icon
  button) + Main badge; `is_authenticated` remains the only access gate.
- Role gating (`app/esi/roles.py`): Director/CEO check via
  `/characters/{id}/roles/`, scope-gated, every failure renders an
  explanatory state on `/corp` (the overview); sub-pages redirect there
  until the gate passes.
- `sync_corporation` (`app/esi/assets.py`): ONE role gate, then three
  kinds — assets, blueprints, jobs — each with its own scope check and
  recorded outcome (`asset_syncs` for assets, `data_syncs` for the rest;
  the per-kind sync-status pattern future kinds reuse). Runs in the
  background tick and the pages' Sync now.
- `/corp/assets` browser (owner-parameterized view layer, region/type
  filters, no owner column); `/corp/blueprints` (bp/bpc icons,
  Original/Copy badges, ME/TE; ESI `quantity` is a sentinel −2/−1/1 and
  never renders; locations resolve via the **asset-snapshot hop** —
  blueprints report their location as the office ITEM id); `/corp/jobs`
  (active by default, `?all=1` history; installer names via tracked
  characters). Wallets remains a stub (deliberate).
- **Office shape learned from live data** (diverged from the original
  `location_flag = "Office"` sketch): offices are type-27 "Office"
  markers (flag `OfficeFolder`/`Office`) whose contents share an
  item-typed container id that is never an asset row. Markers are hidden
  from corp tables/counts; office contents render inside a nested
  "Office" expander; marker-only offices stay listed; the Offices box is
  a static header + note.
- `esi-universe.read_structures.v1` registered + resolver scope-gating:
  only scope-holding characters are tried for structures (a scopeless
  401 never parks and would burn error budget), 404s park like 403s,
  office containers resolve as structures. Live: all four offices
  resolved to their Amamake/Lirerim structures.

**Validation**: passed live — Director main confirmed, 175 corp assets,
129 blueprints, 229 jobs (2 active), offices resolved.

---

**Scope**

- `Character.is_main` flag; "Set as main" action on roster cards, "Main"
  badge. Switching mains switches the targeted corp; old corp data stays
  in the DB, untargeted.
- Corp resolution from the main's `corporation_id` (already persisted).
- ~~Portal prerequisite~~ **Done (2026-11-15)**:
  `esi-characters.read_corporation_roles.v1` is registered on the
  developer portal. Without it, `/characters/{id}/roles/` is a
  guaranteed 403. Remaining follow-through at implementation: the scope
  is in the app's requested set (`.env.example`), and existing
  characters must re-authorize once to actually hold it.
- Role gating: main must hold Director or CEO; otherwise an explanatory
  state (same philosophy as restricted-structure parking — no burning
  the ESI error budget on known 403s).
- Corporation syncs, reusing the owner-agnostic layer unchanged: corp
  assets, corp blueprints, corp industry jobs.
- **Office derivation**: rented offices appear in corp assets as items
  with `location_flag = "Office"`; surface them as the corporate
  inventory locations (the shared pool that corporate build plans draw
  from).

**Schema sketch**

- `characters.is_main` (boolean; single-user app today, one flag
  suffices).
- Synced corp data needs no new tables — `assets`, `asset_syncs` are
  already owner-keyed. New synced tables introduced here (see M2 note on
  the sync family): `blueprints`, `industry_jobs`, keyed
  `owner_type`/`owner_id` like `assets`.

**Validation**: set a Director character as main; corp assets render
under the Corporation section; office stations list; a non-Director main
shows the explanatory role state instead of error spam.

---

## M2 — SDE foundation & blueprint catalog — 🟡 IN PROGRESS

*The foundation half is complete (PRs #15–#16) and landed **differently**
than sketched — read the "landed as" notes; they supersede the original
scope where they conflict. Remaining: the character-side syncs and the
catalog surface.*

**Landed as (PRs #15–#16, 2026-11-16)**

- **The `sde_*` namespace is a verbatim mirror, not app-schema tables.**
  No alembic migration, no ORM models: `app/sde.py` owns the namespace
  wholesale (`DROP` + `CREATE TABLE AS SELECT` per table in one
  transaction), so a dump schema change can never break the import.
  Same columns, same rows, duplicates included. **Interpreting the data
  (blueprint→product joins, skill dedup, activity labels) belongs to the
  consuming query layer, never the import** — an explicit product-owner
  correction from review.
- The YAML-era dump has **no `invBlueprintTypes`**: the registry is
  `industryBlueprints` (typeID, maxProductionLimit); the blueprint→
  product mapping comes from the activity-1 products join at query time.
  Mirrored tables: invTypes, invGroups, invCategories,
  industryBlueprints, ramActivities, industryActivity(+Materials/
  Products/Skills/Probabilities) — 53,925 types, 5,135 blueprints at
  release 2026-11-13.
- Source: fuzzwork's stable-URL gzipped dump
  (`latest-sqlite.db.gz`, ~141 MiB) + `.md5sum` sidecar. `python -m
  app.sde import` (md5 check first, `--file`, `info`).
- **Admin section** (Admin → SDE Data, `app/routes/admin.py`): status
  surface (last check/import/release/outcome/counts) plus Import now
  (forced full re-import, confirm dialog), Check now (cheap md5-only
  check), Pause automatic imports (persisted in `sde_meta.paused`,
  survives re-imports), Stop current import (cooperative cancel between
  download chunks). The background `sde_check_loop` polls hourly, checks
  at most once per 24h (persisted gate), **only maintains an existing
  mirror** — the initial import on a fresh deployment is the admin's
  call — and drop-and-reimports on a changed hash (no diffing).
- Validation passed: the Typhoon recipe reads end to end through the
  mirror (blueprint 998 → ship 644, three buildable components flagged
  for chain continuation, Industry 1, 5.0h base time).

**Landed as (PR #17, 2026-11-16) — the character-side data syncs**

- **Three new per-character kinds** ride the existing per-character
  pass: blueprints, skills, and industry jobs, each with its own scope
  gate and `data_syncs` record (`char-blueprints` / `char-skills` /
  `char-jobs`). A dead refresh token short-circuits the remaining kinds
  — each would only re-attempt the same dead refresh and record the
  same reauth.
- **Character industry jobs landed here**, not with M6 (where they were
  sketched): the plumbing is identical to the other character kinds and
  the owner-keyed `industry_jobs` table already existed, so M6's job
  correlation now has both sides. Character jobs include history, same
  as the corp kind.
- `skills` table (migration 0008): skill_id, trained level, active
  level (implants/boosters — what gameplay math sees), skillpoints.
  Total SP is derived (summed), matching ESI's `total_sp`.
- Skill and blueprint type names resolve at sync time through the
  existing universe resolver (write-once cache, best-effort) — the same
  pattern asset syncs use; pages stay DB-pure.
- **Pages under the Character nav**: `/blueprints`, `/skills`,
  `/jobs` — owner-parameterized versions of the corporation queries
  (`BlueprintRow`/`JobRow` gained `owner_name`; the corp functions are
  now thin single-owner wrappers). `?char=` filter (an unknown id means
  every character), a shared `POST /character/sync` Sync now, and the
  skills page's overview-cards → per-character-sheet split. ESI's
  quantity sentinels never render here either.
- **Generic untyped-location resolution**
  (`UniverseResolver.resolve_location_ids`), from a live-data discovery:
  ESI reports some structure-hangar contents with `location_type "item"`
  naming the structure itself — an id no snapshot can hop, so those
  locations read "Location #id" on every page. Location ids that arrive
  without a usable type (these danglers, blueprint locations) now
  classify by id range — stations below 10¹² answer on the public
  stations endpoint, structures/office containers above it on the scoped
  structures endpoint (the M1 office-container discovery holds there
  too) — and resolve or park like any other location. The asset sync
  resolves dangling item ids through it, and both blueprint kinds
  resolve locations their owner's snapshot can't hop (hop-able ids keep
  naming via their parent, so a parked placeholder can never mask a
  parent's real name). Validated live: five previously-unnamed
  structures resolved across the roster, two parked restricted (no
  docking access anywhere).

**Remaining scope**

- **Catalog surface**: the query layer the M4 planner consumes
  (blueprint search, recipe joins, owned-blueprint overlay). The catalog
  merge rule (SDE name vs `universe_types`) is decided here, at
  consumption time.

**Validation (remaining)**: the catalog query layer reads the Typhoon
recipe through the mirror with owned-blueprint overlay joining live
`blueprints` rows. (The character syncs validated live on the dev
deployment: all characters synced the three kinds ok — 1,099 skills with
game-accurate skillpoints, 754 blueprints with ME/TE, 44 jobs — and the
dangling-structure location fix confirmed against real data.)

---

## M3 — Structure manager

*Where industry happens changes materials, time, and cost — this is the
user-state facility registry the planner multiplies against. Scope note
(2026-11-19): the cost-index sync moved to M15's world-state band, so
M3 is now purely the user-state registry (it consumed world data; it
never belonged to that layer).*

**Scope**

- "Structures" admin page, CRUD per the TODO spec: activity
  (manufacturing/invention/reactions), structure name, structure type
  (NPC station; Raitaru/Azbel/Sotiyo for engineering complexes; Athanor/
  Tatara when activity = reactions), ME rig (none/T1/T2), TE rig,
  system security (high/low/null), solar system (type-ahead against
  `universe_locations`/ESI), tax rate, default-per-activity checkbox.
- Rig/security multipliers: confirm exact values from CCP structure
  docs at implementation time; keep them in one lookup table so balance
  changes are data edits, not code.

**Schema sketch**

- `structures` (user CRUD): name, activity, structure_type, me_rig,
  te_rig, security, system_id, tax_rate, is_default.

**Validation**: create an Azbel with T1 ME/T1 TE rigs in a known null
system; exactly one default per activity is enforced.

---

## M15 — World-state data syncs (public industry & market data)

*Numbered out of sequence on purpose: M-numbers are stable references
across the docs, mockups, and merged history, so this late number sits
with the data-sync track it belongs to. Land it before or alongside the
planner surfaces that consume it — M4's install cost and
contract-backfill peek, the M5/M6 backfill tables, M9's BPC selection
bias.*

*Origin: scoped 2026-11-19 to the public-contracts sync alone; widened
the same day into the cohesive world-state band. The remaining
public-data sync families implement together, as one set of functions
and schema, so the framework decisions — a public-endpoint sync
category, per-family cadence, pruning, rate-limit budget, status
surface — are made deliberately once instead of piecemeal across
consuming milestones. Implementation does not imply consumption: each
milestone reads the data when its surfaces need it, and the landed
character/corp syncs are not retrofitted onto the generalized
framework.*

**Scope**

- **The public-world-data sync category** (the framework slice, landed
  first): public endpoints with no character scopes or role gates,
  unlike the roster kinds (player-structure markets below are the one
  scoped exception, riding the landed gating pattern); per-family
  refresh cadence; pruning/expiry semantics; a `data_syncs` record
  and one admin-visible status view for all public kinds; a deliberate
  rate-limit budget across families. Runs in the background tick like
  the other sync kinds.
- **Cost indices** (moved from M3): sync public `/industry/systems/`
  into `cost_indices` — the M4 install-cost input.
- **Public contracts** (the original M15 scope). The plan-time
  contract-availability window cannot hit ESI live — the
  public-contracts endpoint is per-region by construction with no
  item-level search (the listing carries no contents — verified live
  2026-11-18), so a live scan is a cold sweep of every listing plus
  per-contract items calls (the slowness observed 2026-11-19). The
  sync pays that cost once in the background:
  - Per-region listing sync: `/contracts/public/{region_id}/` into
    `contracts`, over the hub set per the scan-scope decision —
    staged rollout starts with The Forge alone, the five-hub set as
    the expansion target; an all-region sweep remains possible but is
    not the default. Region stays display metadata on planner
    results, never a filter.
  - Candidate pre-filter before any items call: contract type
    `item_exchange` plus the tight volume band (a BPC contract is
    ≈ 0.1 m³). No price filtering — below-market BPCs are finds, not
    noise.
  - Items fetch once per candidate: item-exchange contents are
    immutable once issued, so `/contracts/public/items/{contract_id}/`
    runs a single time per contract into `contract_items` — carrying
    `is_blueprint_copy`, `runs`, `material_efficiency`,
    `time_efficiency`, the fields the BPC selection bias consumes.
    Later listing revalidations only update contract status.
    Expired/finished contracts prune so the tables describe the live
    market.
- **Global market prices** (moved from M10): cached `/markets/prices/`
  (global adjusted/average) into `market_prices`.
- **Regional market orders & history** (folded in 2026-11-19 when the
  market-data region policy resolved the parked region choice — the
  band's heaviest slice): sync `/markets/{region_id}/orders/` and
  `/markets/{region_id}/history/` for the synced hub set, full daily
  history retained append-only. The regional order book is the
  heaviest family in the app — large payloads, continuous churn,
  frequent full 200s even under ETag revalidation — so this slice
  lands last, at a deliberately conservative cadence tuned against
  the rate-limit panel, and **the rollout is staged: The Forge alone
  first** — one region may already brush the limits, and measured
  headroom gates each expansion.
- **Player-structure markets** (the band's one character-scoped
  source): sync `/markets/structures/{structure_id}/` for structures
  on the hub list that the roster can access — the motivating case
  is the corp's Amamake structure (5 Times Nearly Winners) with a
  market module, where the corp will also seed public contracts
  (those arrive via the region scan — no extra contracts work).
  Requires `esi-markets.structure_markets.v1` registered on the
  portal plus one re-auth; only scope-holding characters are tried,
  and 403/404 park per the landed pattern.
- **Observability** (pulled forward from the platform later-track,
  lands with the band): the admin sync-status view plus ESI
  rate-limit and error-budget monitoring — per-group window usage
  recorded from the X-Ratelimit headers the ESILimiter already sees,
  per-family sync duration, and staleness per table. The standing
  requirement: the app never rides its rate limits — the panel exists
  to answer that question continuously while the band soaks.
  Storage-format note (2026-11-19): consider OpenTelemetry
  conventions for the telemetry records so over-time views and
  graphing for API tuning consume them naturally — zero-code Python
  instrumentation
  (<https://opentelemetry.io/docs/zero-code/python/>); the uv
  bootstrap caveat is documented at
  <https://opentelemetry.io/docs/zero-code/python/troubleshooting/#bootstrap-using-uv>.
- ETag-cached GETs through the existing ESI client (`esi_cache`) for
  every family: cold sweeps happen once, later ticks revalidate with
  If-None-Match and are near-free — the mechanism that keeps the
  planning window fast.
- **Schema philosophy**: verbatim-mirror the payloads (the SDE
  lesson — interpretation belongs to the consuming query layer, never
  the sync), so the band never guesses a consumer's queries.
- The planner never calls ESI on the request path — contract
  availability, install cost, and price lookups read these tables
  only (page-render purity holds).

**Schema sketch**

- `contracts` (synced public data): contract_id, region_id, type,
  volume, price, issuer_id, date_issued, date_expired, status.
- `contract_items` (synced): contract_id, type_id, quantity,
  is_blueprint_copy, runs, material_efficiency, time_efficiency.
- `cost_indices` (synced): system_id, activity, cost_index.
- `market_prices` (synced): type_id, adjusted_price, average_price.
- `market_orders` (synced): region_id, order_id, type_id, system_id,
  location_id, is_buy_order, price, volume_remain, issued, expires.
- `market_history` (synced): region_id, type_id, date, average,
  highest, lowest, order_count, volume.
- `sync_hubs` (user state — the band's one piece of it): the synced
  market sources — seeded with The Forge alone (staged rollout),
  extensible with custom region hubs and accessed player structures.

**Validation**: a sweep against live ESI lands the real The Forge
Charon contract (2026-11-19: ten 1-run ME 10 / TE 20 BPCs at 300M)
with its BPC fields intact; the cost-index lookup returns a known
system's manufacturing index; `market_prices` carries both price
fields for a sampled type; the rate-limit panel shows per-group
headroom with The Forge alone live — the gate for adding the next
region; once Metropolis joins the hub set, an Amamake system filter
over its orders returns local prices and the 5 Times Nearly Winners
structure market syncs through its scoped source; history appends
one row per type per region per day without rewriting; an immediate
second sweep revalidates on ETags (304s, seconds not minutes); the
admin status view shows every public kind with its rate-limit usage;
the planner's contract-availability query for the Charon Blueprint
answers entirely from the DB.

---

## M4 — Planner: single-blueprint calculation

*The calculator core, before any chaining. One blueprint, one activity,
real numbers. This and M5 are the substrate the M9 distribution engine
consumes — the per-node skill and time math decided here is what the
assignment weighting later multiplies against.*

**Scope**

- Planner entry: search + select a blueprint — from owned blueprints
  (pre-filled ME/TE from the `blueprints` table) or from the SDE catalog
  (manual ME/TE entry for BPOs you'd train up to).
- Inputs: number of runs, ME/TE, facility (structure-manager default
  for the activity, overridable). Run count is bounded by the
  blueprint's max production limit (SDE
  `industryBlueprints.maxProductionLimit`) — in practice around 30
  days of output per job, the game's job-duration ceiling. **Run
  math divides required units by products-per-run** (SDE
  `industryActivityProducts.quantity` — components yield 3/run,
  fuel blocks 40/run); runs = ⌈units ÷ products-per-run⌉.
- Outputs per material: base quantity → adjusted for blueprint ME,
  facility/rig material bonuses, security multipliers (SDE math:
  rounding is round-half-up at the end of the multiplier chain — pin
  exact formula behavior with tests against known values).
- Outputs overall: production time (activity duration × TE × rig time
  bonus × skill modifiers from the character running it — character
  selector feeds the skills table), install cost (base input value ×
  system cost index + structure tax).
- **Copy-time math**: per-run copy time (SDE activity 5) for any
  blueprint — the input M9's copy planning and M12's BPO
  recommendations multiply against. Copy time is typically ~80% of
  base build time per run, which is what makes copying a parallelism
  lever with sharp diminishing returns.
- **Skill→time multipliers live in a data table here** (like the rig
  multipliers): which skills reduce which activities' time, whether
  copying is affected, pinned from dogma/CCP docs at implementation.
  The time-balanced model in `reference/chains/TYPHOON-CHAIN.md` (built on a ×0.68
  manufacturing assumption) is the golden-value check.
- Character skills matter here: Industry (time), Advanced Industry
  (time), facility-relevant skills. Slot-count skills and
  remote-range skills are consumed in M9, not here.

**Validation**: a known Typhoon BPO at ME 10 in a defined Azbel
reproduces hand-checkable material counts, time, and install cost
against in-game numbers.

---

## M5 — Planner: full chain resolution & phase view

*The recursive BOM explosion — the heart of the system. Turns one
blueprint into an ordered set of production phases. This is the
reverse-then-rebuild of the end goal: raw-material inputs on one end,
the layered chain the distribution engine schedules on the other.*

**Scope**

- Chain resolution: walk the target's manufacturing inputs; any input
  that *is* a blueprint product recurses. Compute phase depth per node —
  **phases count up in build order** (decided 2026-11-18): raw-material
  terminators sit at phase 0, a node's phase is 1 + max(its inputs'
  phases), and the target lands at the highest phase number. Detect and
  refuse blueprint cycles defensively (SDE shouldn't contain any for
  manufacturing, but the resolver shouldn't trust it).
- **Chains generate dynamically at plan time** (clarified 2026-11-19):
  the resolver builds every chain from the selected target and count on
  each calculation — nothing enumerates or ships chains ahead of
  selection (the requirement overview resolves at selection per the
  planner-overview decision). The `reference/chains/` documents are
  validation anchors — golden values the resolver gets checked against —
  never pre-generated inputs to the planner.
- **Reaction resolution in the initial chain** (moved here from M7,
  2026-11-16): the resolver walks reaction formulas (SDE activity 11)
  exactly like manufacturing — any reaction input that is itself a
  product recurses, whatever the activity. The Typhoon chain exercises
  this for real: its components take reaction intermediates
  (Pressurized Oxidizers, Reinforced Carbon Fiber) whose own recipes
  are a further reaction layer consuming fuel blocks (manufacturing)
  and moon materials. Reaction-capable facilities and rigs are
  already modeled by M3's structure manager.
- **Chain terminators classified**: not every input is buildable —
  the Typhoon chain bottoms out in minerals, moon materials, and PI
  commodities (Chiral Structures, Test Cultures, … — reactions in
  particular commonly take planetary inputs). Terminators are leaf
  nodes; the resolver must recognize them rather than treat "no
  blueprint found" as an error. Planning deliberately stops at the
  raw material input: *how* it's obtained — reprocessed ore (we plan
  tritanium, never veldspar), planetary industry, moon mining, or
  market purchase — is out of scope for the build planner. (A later
  track adds reprocessing yield math on top of the acquisition table
  — see Later tracks.)
- Shared-quantity aggregation: the same intermediate type required by
  multiple parents merges into one node with summed requirements, then
  rounds *its* runs/materials once — per-phase, not per-parent.
- Phase-grouped view: expandable tree per phase, node rows showing
  required qty, activity, and the blueprint involved — the assets-page
  collapsible patterns. **Tree shape of record** (confirmed
  2026-11-16): the root is the target build item with its count;
  every branch's input requirements multiply up to meet that count;
  the final branches are raw material inputs. Each node carries its
  quantity (multiplied to the target count), its activity, and — via
  the overlays below — blueprint ownership and asset availability.
  The fully expanded Typhoon chain — every branch, no elision, plus
  the aggregated phases and raw-material totals — lives in
  `reference/chains/TYPHOON-CHAIN.md` (too heavy to inline here; it's the reference
  output M5's implementation gets checked against).
- **Blueprint availability overlay**: per node, whether a usable
  blueprint is owned (char + corp, from the `blueprints` table — with
  runs ≥ 0 for copies, ME/TE for originals) and where it sits; missing
  blueprints called out distinctly.
- **Asset availability per node**: required vs. on-hand, measured
  against the selected inventory pool — personal (characters in the
  plan) and/or corporate (main's corp offices, from M1). Per-type
  aggregation patterns already exist (`structure_page`).
- Chain-level output: total materials per phase, total time, total
  install cost.
- **Chain timeline view**: a linear (Gantt-style) rendering of the
  resolved chain parameterized by target count — phase bars, copy
  pipelines, and the dead zones where builds wait on inputs or BPCs
  (the `reference/chains/TYPHOON-CHAIN.md` timelines as an app surface). Durations
  come from M4's time math; the view makes the gating resource
  visible at a glance.
- **Raw-material acquisition table**: the chain's terminators summed
  across all components into one totals table, grouped by category —
  minerals, moon materials, PI commodities, ice products — so the
  planner knows exactly what to obtain and via which in-game mechanic
  (market, planetary industry, mining, reprocessing). The Typhoon ×1
  version is in `reference/chains/TYPHOON-CHAIN.md`.

**Validation**: the Typhoon chain resolves to the expected phases
(components → reaction intermediates → second reaction layer +
fuel blocks → minerals, moon materials, and PI commodities — user
confirms phase structure and quantities), blueprint availability
matches what's actually owned, and a corp-pool measurement sees office
inventory.

---

## M6 — Build plans: export, track, complete

*Persists a resolved chain as a living document and measures it against
reality over time.*

**Scope**

- Export from the planner: snapshot the resolved chain (nodes, phases,
  quantities, facility choices, the ME/TE and runs inputs) into
  `build_plans` / `build_plan_nodes`, **including the schedule** —
  login-window length, job waves, BPC run counts, and copy-pipeline
  state at export time. The snapshot is the plan of
  record; re-running the planner makes a *new* plan, it doesn't mutate
  an old one.
- "Build Plans" section: list + detail views, personal and corporate
  plans (corporate = main's corp as the inventory pool).
- Progress tracking: node-level required / available / delivered
  against the plan's inventory pool, refreshed from asset syncs
  (page-render purity rule holds: views read DB only).
- **Industry-job correlation**: match `industry_jobs` (char + corp,
  synced from M1/M2) to plan nodes by blueprint + output type +
  location; show installed jobs on their nodes, and pull completion
  status from job state. (Heuristic matching is fine — the endpoint
  has no plan reference; over-precision isn't worth it.)
- Plan states: draft → active → complete (all leaf nodes delivered) /
  abandoned.

**Schema sketch**

- `build_plans`: id, name, target type_id, runs, params snapshot
  (JSON), pool (personal/corp), status, timestamps.
- `build_plan_nodes`: plan_id, phase, type_id, activity, required qty,
  blueprint ref, produced/available/delivered (materialized by sync for
  cheap page renders).

**Validation**: export a Typhoon plan, install one component job
in-game, watch the job appear on its node and the phase progress move
when it delivers.

---

## M7 — Reactions — folded into M5 (2026-11-16)

*Revised when the validation chain was checked against the live
mirror: the Typhoon chain itself requires two reaction layers, so
reaction resolution belongs to the initial chain (M5), not a post-M6
extension. Reactions commonly occupy the early, deep portions of even
T1 product chains. This section stays as a record of the original
plan.*

What the fold means concretely: the M5 resolver treats reaction
formulas (SDE activity 11) like any other blueprint product and
recurses through them; reaction-capable facilities/rigs were already
in M3's structure manager; reaction skills feed M4's time math like
any other skill modifier. Nothing of the original scope survives as
separate work — the activity-generic schema from M2 absorbed it as
designed.

---

## M8 — Invention & T2/T3 chains

*Full-chain ambition: any buildable thing resolvable end-to-end.*

**Scope**

- Invention resolution: T2/T3 blueprint copies as invention *products*
  of their T1/T3 relic counterparts — `sde_activity_probabilities`,
  decryptor selection (yield modifiers: ME/TE/runs/probability), and
  expected-value math (probabilistic runs: "runs needed" computed with
  success probability, presented as expected + confidence range).
- T3 reverse engineering from ancient relics (same activity family in
  the SDE; loaded since M2). **T3's interface with invention/reverse
  engineering is to-be-determined** — the author doesn't have
  significant T3 production experience, so the T3 portions of this
  milestone get designed at pickup (against SDE data and community
  docs) rather than pre-planned in detail here.
- Chain view gains probabilistic nodes: an invention node shows the
  underlying copies required and the decryptor choice.
- Subsystem/hull interdependencies for T3 ships (hull + subsystems
  planned together as one target set).

**Validation**: a T2 ship (e.g. a Panther, since the Typhoon chain is
known — its T2 variant) resolves from moon reactions through component
invention through manufacturing to the ship, with the Typhoon-chain
knowledge as the sanity anchor.

---

## M9 — Job orchestration: slots, skills, capsuleers

*The coordination layer: who installs what, when, from where — the
work-distribution core of the end goal. A logic proof-out of the
target behavior — Typhoon ×100 spread across the live corp roster's
slots, with model rules and assumptions — is in `reference/chains/TYPHOON-CHAIN.md`.*

**Scope**

- Job-slot math per character per activity, from synced skills
  (manufacturing: Mass Production family; science jobs: Laboratory
  Operation family; reactions: reaction skills) — confirm exact
  skill → slot mapping from SDE dogma/CCP docs at implementation and
  keep it in a data table like the rig multipliers.
- Live slot occupancy: subtract synced `industry_jobs` (char + corp)
  from each character's slot ceiling per activity.
- **Blueprint job-lock**: a blueprint (original or copy) supports
  exactly one active job — concurrency per commodity is
  min(slot pool, blueprint count), never slots alone. With one BPO
  per reaction formula per character, a formula runs at most 3
  concurrent jobs however many reaction slots are free; copying is
  likewise one job per BPO. Slot math multiplies against blueprint
  availability (the structural discovery of the `reference/chains/TYPHOON-CHAIN.md`
  time-balanced model: reactions and copying are BPO-bound, slots
  idle).
- **Login-window alignment**: jobs sized to end together at window
  boundaries (the deliver-together objective) — even-split run
  counts, window length a plan parameter (the proof-outs used 6h).
  Fewer, larger jobs trade install frequency against end-time
  spread; the sizing rule is the v2 model's.
- **Efficiency-weighted per-phase job assignment**: for each phase, a
  suggested split of its nodes' jobs across participating capsuleers.
  Eligibility first (required skills from `sde_activity_skills`,
  slots available), then a weighted distribution: characters whose
  skill sets build a given component more efficiently get higher
  weight for that component's nodes. Suggestions are user-editable
  before export.
- **Profit-vs-throughput control**: the plan-level slider, **three
  positions** (2026-11-18) — **profit**: efficiency-weighted
  assignment, concentrate work on the builders whose skills reduce
  input materials, everything in-corp; **balanced**: farming — farm
  chain portions out to friends at below-market rates; **throughput**:
  purchase whatever shortens wall time and fill every available build
  slot to minimize time-to-completion of what the next stage needs.
  One slider for the whole chain to start; per-stage control is a
  possible later refinement.
- **Copy & BPC planning**: the mechanism for parallel installation —
  the planner recommends how many BPCs to copy from the owned BPOs
  and each copy's run count, so the jobs spread across multiple slots
  and characters. The tradeoffs are modeled explicitly:
  - A single job at maximum runs is always the most
    material-efficient way to produce a commodity, but takes the
    longest; splitting across more slots/characters means more jobs
    with fewer runs each, and per-job material rounding (M4's math)
    erodes efficiency as the split grows.
  - Copy time is a real cost in the schedule — copies must finish
    before any manufacturing job installs, and copy jobs themselves
    consume science slots from the same characters' budgets.
  - Diminishing returns apply: 30 one-run BPCs will not beat 3
    ten-run BPCs once copy time is counted. The recommendation finds
    the balance point, informed by the slider.
  - **Copy-vs-direct is a timed, skill-dependent decision** (rule
    and worked example in `reference/chains/TYPHOON-CHAIN.md`): copy while
    input-starved (the dead zone before a phase's inputs exist);
    build direct from the BPO once inputs flow, if the runner's
    skilled build time beats copy time per run (break-even
    multiplier ≈ 0.8 for the T1 components). Low-skill characters
    should keep copying; max-skill characters should switch — an
    efficiency weighting the assignment engine encodes.
    **Seesaw edge case** (2026-11-18, from the ×10 simulation):
    purchasing upstream shrinks T_in, evaporating the dead zone that
    makes copying free — an upstream purchase can flip the
    copy-vs-direct verdict for downstream nodes (the overflow grows
    as the dead zone shrinks). Every Purchase ⇄ Build toggle is
    therefore a full chain re-derivation, never a local patch.
  - Run counts are bounded: each blueprint carries a maximum run
    limit (SDE `industryBlueprints.maxProductionLimit`) — large, in
    practice capping a single job around 30 days of output, since
    jobs generally cannot last longer than that. Multiple BPOs of
    the same type may exist, each with its own ME/TE, so a split can
    draw across several originals (see the M5 blueprint-selection
    open question).
- Remote installation ranges: Supply Chain Management (manufacturing)
  / Scientific Networking (research-family) skill levels vs. job
  location — flag jobs a character can't install remotely and where
  they'd need to be.
- Per-character job lists: "what you should install next" per phase —
  the capsuleer-facing view of the plan.

**Validation**: with two registered characters of differing skills,
phase assignment respects slots and required skills, and the slider's
two ends demonstrably move the same node's work (efficiency end: the
more-skilled builder; throughput end: both); blueprint job-lock is
respected (a formula held as one BPO per character never exceeds 3
concurrent jobs); for a known split, the recommended BPC count and
run counts are sane with copy lead time visible in the schedule; a
character without the remote-install skill for the facility's system
gets flagged, not silently assigned.

---

## M10 — Market pricing & build-vs-buy (deferred by decision)

- Analysis only — every price pipeline (global prices, regional
  orders/history) syncs in M15's world-state band; the region policy
  is decided (2026-11-19: five NPC hub regions plus custom hubs, The
  Forge default, plan-time region selector among synced regions), so
  this milestone has no open sync questions. What remains here is the
  consumption: build-vs-buy per node and per material, and target
  profitability, over M15's local tables.
- Build-vs-buy per node and per material: compare chain-adjusted build
  cost against market buy; mark nodes where buying beats building.
- Target profitability: product sale value (market sell) vs. full
  chain cost.

## M11 — Interactive chain DAG

- Node-graph view of the resolved chain (SVG/JS), layered by phase,
  alongside (not replacing) the phase-grouped views. Hover for node
  detail, click through to node rows. Reuses plan data; presentation
  only.

---

## The post-core fork

Once M12 lands, the roadmap forks into two **equal-weight
alternatives** — external distribution (M13) or in-corp efficiency
gains (M14). They are deliberately not sequenced against each other;
the product owner decides at pickup which is the higher priority.
M10's market pricing is a dependency of M14 only.

## M12 — Capability analysis & recommended end products

*The fork-point substrate: what this corporation is actually
positioned to build, and what it's missing.*

**Scope**

- **Catalog-wide capability match**: the corp's registered characters
  (synced `skills`) and owned blueprints (`blueprints`, char + corp)
  joined against the buildable catalog — per product, whether every
  chain layer is producible in-corp, and if not, exactly which
  intermediates are blocked and why (missing skills, missing
  blueprints). The match resolves lazily against the recipe graph,
  per target on demand — never by pre-expanding the catalog's chains
  (chains generate at plan time; see M5's clarification).
- **Recommended end products**: ranked suggestions of what the
  corporation should produce — fully buildable targets first, and
  partially buildable ones with their gaps surfaced (a target whose
  intermediates can't be built in-corp may not make sense to produce
  internally, or may be a farming candidate — see the fork).
- **Per-target gap report**: for any selected target, the node-level
  list of missing skills (who could train them) and missing
  blueprints — the same gap list both fork branches respond to
  (train, farm out) and the input the end-goal loop closes on.
- **Blueprint asset gap analysis** (noted 2026-11-17; rules and
  worked example in `reference/chains/TYPHOON-CHAIN.md`): BPO obtainment
  recommendations from the chain resolver's phase math plus the
  synced `blueprints` table — per commodity, minimum useful BPOs =
  ceil(copy-queue rate ÷ input-dead-zone rate), the target-count
  trigger where the queue starts overflowing the dead zone, the
  slot-saturation ceiling, and the acquisition ladder with
  days-saved per rung. All closed-form and scale-invariant in the
  target count; cost-checked against market pricing (M10) once that
  exists, so recommendations read as "this BPO buys N days."

**Validation**: against the live roster, a fully-covered T1 target
(e.g. the Typhoon chain) reports producible end to end; a target with
a known gap (e.g. freighter-capable character without the
intermediate-component skills or blueprints) reports exactly the
blocked intermediates and the reason.

## M13 — Fork branch: skill gap analysis & training recommendations

*In-corp efficiency gains: close the gaps the M12 report finds by
training the roster toward the target.*

**Scope**

- Per-character skill plans for a selected target build: the gap
  between current synced skills and the chain's requirements
  (eligibility) plus the skills that carry efficiency gains
  (material/time), ranked by impact on the target's overall
  efficiency.
- Training recommendations presented per character (what to train,
  toward which node's requirement or efficiency gain), working from
  the M12 gap report.
- **Skill→efficiency mapping is resolved empirically here**: once the
  efficiency math exists, attempting a complex build (T3 destroyer,
  Carrier chain) self-answers which skills carry efficiencies worth
  training — validation targets, not pre-research. T1 skill gains
  are time reduction only; T3 components and advanced reactions have
  material gains.

**Validation**: run the analysis against a complex chain (T3
destroyer or Carrier) with the live roster; the recommendations
surface the skills with real efficiency impact for that chain, and
training-path suggestions are sane against the skill queue data
already synced.

## M14 — Fork branch: capsuleer bidding & contract farming

*External distribution: farm chain portions out to friends as paid
contracts. Depends on M6 (plans), M10 (market pricing), M12 (the gap
report says what to farm), and the multi-user platform track (TODO) —
other capsuleers must be able to log in. Farming is the plan-level
slider's balanced middle position (2026-11-18): the same wall-time win
as purchasing components, at below-market cost — the framing that
connects this fork branch to the posture control in the end goal.*

**Scope**

- **Marking plan nodes for farming**: within one build plan, the
  planner marks what "we" build vs what gets farmed out — on
  complicated chains some layers make more sense to farm than others.
  Bid requests are slices of a plan, not separate artifacts.
- **Publish a request**: target output, quantity, the hangar where
  the providing blueprints sit, and a delivery window.
- **Delivery window**: an adjustable human-manageable floor delivery
  time *plus* the actual build time (e.g. 2 days + 1 hour of build,
  or 2 days + 2 days of build) — balanced so the planner isn't
  waiting indefinitely but the producer has realistic hours to
  produce and deliver. Not a percentage multiplier (those misbehave
  at the extremes).
- **Bid pricing**: defaults derived from market rates at the input
  hub (e.g. Jita) — starting point is the buy rate, often a
  buy/sell "split" rate; user-adjustable. The planner's edge is
  acquiring inputs below market sell.
- **No efficiency math**: efficiency is the bidder's problem; the
  system only prices and tracks.
- **Accept → deliver → paid**: a capsuleer accepts a portion of the
  chain in-app, delivers via in-game contract at the pre-agreed
  rate, and is paid on contract completion. The app tracks contract
  state only — isk settlement happens in-game; this is a
  record/tracking layer, not a payment layer.

**Validation**: publish a one-stage request from a Typhoon plan with
a blueprint in a corp hangar, have a second account claim and produce
it, and see delivery reflected on the plan node and the payout
recorded.

---

## Later tracks (from TODO, not re-planned here)

- **Reprocessing & acquisition efficiency** (noted 2026-11-16):
  extends M5's raw-material acquisition table from "what to obtain"
  into "how much ore/ice to process for it" — yield math for
  reprocessing compressed veldspar et al. from character skills,
  implants, and structure bonuses (rigs, faction-warfare system
  bonus, security status). Deliberately out of the chain planner,
  which stops at the raw material input; this is a standalone
  calculator against the acquisition table. Natural pairing with
  M13's skill recommendations (Reprocessing skill family).
- **Platform / administration**: local user accounts, admin menu,
  observability. Becomes a prerequisite once more than one human uses
  the app (and a hard one for M14's bidding). The sync-observability
  slice (sync status, rate limits, staleness) is pulled forward out
  of here into M15's world-state band (2026-11-19) — the rest of the
  track stays put.
- **CI Node 20 deprecation bump** and the smaller TODO items — stay in
  `TODO.md`.

---

## Open questions (park, decide at milestone pickup)

- Catalog merge rule details (SDE name vs. `universe_types` resolved
  name) — M2.
- One plan, multiple facilities: does a plan pin every node's facility
  at export, or re-pick facilities as the plan progresses? — M6.
- Blueprint selection policy when several copies/BPOs exist — BPOs
  may be duplicated, each with its own ME/TE, alongside copies of
  varying runs (best ME? most runs? user pick?) — M5.
- Can corporate plans draw from members' personal inventories as a
  fallback pool, or strictly the corp offices? — M5/M6.
- Invention: fixed decryptor choice per plan vs. comparing decryptor
  EVs in the planner UI — M8.
- Skill→efficiency mapping (which skills carry material vs time
  gains, per activity) — resolved *empirically* at M13 by targeting a
  complex build (T3 destroyer, Carrier) once the efficiency math
  exists, not by pre-research. T1 = time reduction only; T3
  components and advanced reactions have material gains.
- T3 production mechanics: how subsystems, relics, and reverse
  engineering actually interface with the invention family — design
  at M8 pickup; the author's T3 production experience is thin, so
  validate against SDE data and community documentation then.
- Pipelining semantics: partial phase deliveries (reaction chunks
  feeding early component builds, BPCs building as they finish
  copying) vs. strict phase-serial deliver-together — the
  `reference/chains/TYPHOON-CHAIN.md` proof-outs are deliberately serial; pipelining
  is the known next refinement and would shrink every dead zone,
  but complicates the scheduler and the delivery story. Decide at
  M9 pickup whether v1 ships serial-only.
- Recurring commodities across phases (surfaced by
  `reference/chains/CHARON-CHAIN.md`, 2026-11-18): the same type can
  appear in multiple phases when its consumers sit at different
  depths (Charon: fuel blocks at phases 1–3, PO/RCF at 3–4). Build
  one merged campaign at the earliest need, or per-phase campaigns?
  Merged is simplest but ties up inputs early; per-phase is
  pipelining-adjacent. — M5/M9.
- Mixed-activity phases (surfaced by `CHARON-CHAIN.md`): phases that
  mix manufacturing and reaction items schedule through the
  slot-hour formula in the reference model (the BPO-bound reaction
  branch only triggers for all-reaction phases). Refine for mixed
  phases. — M9.
- Plan re-planning semantics: mid-flight adjustments (add runs, swap a
  facility) — amend in place vs. fork a new plan — M6.
