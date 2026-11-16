# Milestones — Industry Planner

The build-out plan for the industry planner, derived from `TODO.md` (which
stays the surface for small items and ideas). Each milestone carries its
goal, scope, and a validation step, so a session can pick one up and go.
Order matters within a track, not across all of them — dependencies are
called out explicitly.

Validation case throughout: the **Typhoon** (T1 battleship) blueprint. The
chain it produces (ship → components → base minerals) is familiar ground
and exercises phases, blueprint availability, and asset measurement
without needing invention or reactions.

---

## Status (updated 2026-11-16)

| Milestone | State |
|---|---|
| M1 — main character & corporation pool | ✅ **Complete** (PRs #12–#14) |
| M2 — SDE foundation & blueprint catalog | 🟡 **In progress** — SDE foundation + admin self-update (PRs #15–#16) and the character-side data syncs (PR #17) complete; remaining: catalog surface |
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
buildable components, Industry 1, 5.0h base).

---

## Architecture: three data layers

Every planner feature is a join across exactly these layers. Keeping the
split crisp is what lets T2/T3 and reactions arrive later as *data and
resolver extensions* instead of schema rewrites.

| Layer | Source | Nature | Examples |
|---|---|---|---|
| **Static (recipes)** | EVE SDE, imported | Write-once per EVE release | blueprint → materials, products, required skills, activity durations, invention probabilities |
| **Dynamic (world state)** | ESI, ETag-cached sync | Refreshed in background | owned blueprints (ME/TE/runs), skills, industry jobs, system cost indices, assets, market prices (deferred) |
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
  engineering — via a generic activity dimension. V1 *resolves* only the
  T1 manufacturing chain; the others land incrementally (reactions
  first, per the v1-scope decision) without migrations that retrofit
  activity types.

### Decisions already made

- **SDE source**: managed import command — downloads the fuzzwork SQLite
  dump for the current EVE release and mirrors it verbatim (see M2's
  landed-as notes). Re-run per release; nothing checked into git.
  Landed 2026-11-16 with the admin self-update.
- **V1 chain scope**: T1 manufacturing only; reactions are the first
  extension; invention/T2 and T3 follow. Schema supports all from the
  start.
- **Market pricing**: deferred (separate milestone, near the end). The
  planner computes materials, time, and install cost from tax + system
  cost index; build-vs-buy and profitability come with the market
  pipeline.
- **Visualization**: phase-grouped expandable views first (reusing the
  assets-page collapsible-row patterns); interactive node-graph DAG is
  its own follow-up milestone.

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

## M3 — Structure manager & cost indices

*Where industry happens changes materials, time, and cost — this is the
user-state facility registry the planner multiplies against.*

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
- System cost indices: sync public `/industry/systems/` into
  `cost_indices` (system_id, activity, cost_index), cached like other
  universe data. Refresh cadence with the sync loop.

**Schema sketch**

- `structures` (user CRUD): name, activity, structure_type, me_rig,
  te_rig, security, system_id, tax_rate, is_default.
- `cost_indices` (synced public data).

**Validation**: create an Azbel with T1 ME/T1 TE rigs in a known null
system; the cost-index lookup returns that system's manufacturing
index; exactly one default per activity is enforced.

---

## M4 — Planner: single-blueprint calculation

*The calculator core, before any chaining. One blueprint, one activity,
real numbers.*

**Scope**

- Planner entry: search + select a blueprint — from owned blueprints
  (pre-filled ME/TE from the `blueprints` table) or from the SDE catalog
  (manual ME/TE entry for BPOs you'd train up to).
- Inputs: number of runs, ME/TE, facility (structure-manager default
  for the activity, overridable).
- Outputs per material: base quantity → adjusted for blueprint ME,
  facility/rig material bonuses, security multipliers (SDE math:
  rounding is round-half-up at the end of the multiplier chain — pin
  exact formula behavior with tests against known values).
- Outputs overall: production time (activity duration × TE × rig time
  bonus × skill modifiers from the character running it — character
  selector feeds the skills table), install cost (base input value ×
  system cost index + structure tax).
- Character skills matter here: Industry (material waste), Advanced
  Industry (time), facility-relevant skills. Slot-count skills and
  remote-range skills are consumed in M9, not here.

**Validation**: a known Typhoon BPO at ME 10 in a defined Azbel
reproduces hand-checkable material counts, time, and install cost
against in-game numbers.

---

## M5 — Planner: full chain resolution & phase view

*The recursive BOM explosion — the heart of the system. Turns one
blueprint into an ordered set of production phases.*

**Scope**

- Chain resolution: walk the target's manufacturing inputs; any input
  that *is* a blueprint product recurses. Compute phase depth per node
  (base materials = deepest, target = phase 0); a node's phase is
  max(dependency phases) + 1. Detect and refuse blueprint cycles
  defensively (SDE shouldn't contain any for manufacturing, but the
  resolver shouldn't trust it).
- Shared-quantity aggregation: the same intermediate type required by
  multiple parents merges into one node with summed requirements, then
  rounds *its* runs/materials once — per-phase, not per-parent.
- Phase-grouped view: expandable tree per phase, node rows showing
  required qty, activity, and the blueprint involved — the assets-page
  collapsible patterns.
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

**Validation**: the Typhoon chain resolves to the expected phases
(components then minerals, per the known build chain — user confirms
phase structure and quantities), blueprint availability matches what's
actually owned, and a corp-pool measurement sees office inventory.

---

## M6 — Build plans: export, track, complete

*Persists a resolved chain as a living document and measures it against
reality over time.*

**Scope**

- Export from the planner: snapshot the resolved chain (nodes, phases,
  quantities, facility choices, the ME/TE and runs inputs) into
  `build_plans` / `build_plan_nodes`. The snapshot is the plan of
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

## M7 — Reactions (first chain extension)

*Extends the resolver from manufacturing-only to manufacturing +
reactions. The activity-generic schema from M2/M5 pays off here.*

**Scope**

- Reaction chain resolution: SDE activity "reactions" — inputs are
  mined moon materials and/or reaction products; refineries (Athanor/
  Tatara) as facilities with reaction rigs; reaction skills for time.
- Fuel-block and simple/complex reaction chains resolve as phases
  feeding manufacturing parents.
- Facility picker gains reaction-capable structures (already modeled in
  M3's activity-conditional structure types).

**Validation**: a chain that combines reactions and manufacturing —
e.g. a T2-adjacent component whose advanced materials come from
reactions — resolves with reactions in the correct early phases.

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
  the SDE; loaded since M2).
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

*The coordination layer: who installs what, when, from where.*

**Scope**

- Job-slot math per character per activity, from synced skills
  (manufacturing: Mass Production family; science jobs: Laboratory
  Operation family; reactions: reaction skills) — confirm exact
  skill → slot mapping from SDE dogma/CCP docs at implementation and
  keep it in a data table like the rig multipliers.
- Live slot occupancy: subtract synced `industry_jobs` (char + corp)
  from each character's slot ceiling per activity.
- **Per-phase job assignment**: for each phase, a suggested split of
  its nodes' jobs across participating capsuleers — slots available,
  skills held (blueprint-required skills from
  `sde_activity_skills`), and then simple round-robin or
  load-by-slots. Suggestions are user-editable before export.
- Remote installation ranges: Supply Chain Management (manufacturing)
  / Scientific Networking (research-family) skill levels vs. job
  location — flag jobs a character can't install remotely and where
  they'd need to be.
- Per-character job lists: "what you should install next" per phase —
  the capsuleer-facing view of the plan.

**Validation**: with two registered characters of differing skills,
phase assignment respects slots and required skills; a character
without the remote-install skill for the facility's system gets
flagged, not silently assigned.

---

## M10 — Market pricing & build-vs-buy (deferred by decision)

- Price pipeline: cached `/markets/prices/` (global adjusted/average)
  plus regional orders/history; region choice was explicitly deferred —
  revisit default (The Forge vs. plan-time selector) when this
  milestone is picked up.
- Build-vs-buy per node and per material: compare chain-adjusted build
  cost against market buy; mark nodes where buying beats building.
- Target profitability: product sale value (market sell) vs. full
  chain cost.

## M11 — Interactive chain DAG

- Node-graph view of the resolved chain (SVG/JS), layered by phase,
  alongside (not replacing) the phase-grouped views. Hover for node
  detail, click through to node rows. Reuses plan data; presentation
  only.

## Later tracks (from TODO, not re-planned here)

- **Platform / administration**: local user accounts, admin menu,
  observability. Becomes a prerequisite once more than one human uses
  the app.
- **CI Node 20 deprecation bump** and the smaller TODO items — stay in
  `TODO.md`.

---

## Open questions (park, decide at milestone pickup)

- Catalog merge rule details (SDE name vs. `universe_types` resolved
  name) — M2.
- One plan, multiple facilities: does a plan pin every node's facility
  at export, or re-pick facilities as the plan progresses? — M6.
- Blueprint selection policy when several copies/BPOs exist (best ME?
  most runs? user pick?) — M5.
- Can corporate plans draw from members' personal inventories as a
  fallback pool, or strictly the corp offices? — M5/M6.
- Invention: fixed decryptor choice per plan vs. comparing decryptor
  EVs in the planner UI — M8.
- Plan re-planning semantics: mid-flight adjustments (add runs, swap a
  facility) — amend in place vs. fork a new plan — M6.
