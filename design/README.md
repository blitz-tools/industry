# Design — build planner mockups

Per-chain wireframe sets under `design/<target>/` — one directory per
simulation target, matching the `reference/chains/<TARGET>-CHAIN.md`
document it visualizes. Shared styles and components live in
`design/shared/` so every set renders identically.

| Directory | Set |
|---|---|
| `typhoon/` | planner → build plan → active plan — the **reference standard** |
| `charon/` | planner → build plan → active plan (capital stress test) |
| `panther/` | planner + scoped variant → build plan → active plan (invention set) |
| `jackdaw/` | planner → build plan → active plan (T3 relic-invention set) |
| `trimark/` | planner → build plan → active plan (T2 rig set — retry loop) |
| `rage/` | planner → build plan → active plan (T2 ammo set — run pool + residue) |
| `crash/` | planner → build plan → active plan (reaction-terminal set — cross-drug DAG) |
| `hel/` | planner → build plan → active plan (supercarrier set — convergence chain) |
| `tfi/` | planner → build plan → active plan (faction set — LP acquisition) |
| `ragnarok/` | planner → build plan → active plan (titan set — the absolute stress test) |
| `structures/` | single surface page — the M3 facility-registry CRUD (registry table, form, sync import, multiplier reference) |

These are design artifacts for iteration, **not** app code: no build
step, no JS, nothing wired to the FastAPI app. They are deliberately
kept out of `docs/` so the Zensical site never publishes them (they
contain live character and corporation names).

## The mockup convention (binding)

The Typhoon set is the target reference. Every chain gets **the same
pages, layout, components, and visual language — only the data
changes**. Do not invent per-chain visuals or restyle components: a
reader moving between sets should need zero re-orientation. New
components or layout changes are proposed once against the reference
set; once settled they apply to every set (decisions graduate to
`MILESTONES.md` per the flow in `AGENTS.md`).

- Styles come from `../shared/mockups.css` — design tokens and
  component shapes copied from `app/static/style.css`, which remains
  the styling source of truth.
- **Planner entry is commodity-first** (2026-11-20 decision of
  record, MILESTONES.md): search and target are the built commodity +
  unit count; the producer blueprint is a derived input named in the
  autocomplete sub-line and target card. Every set's planner follows
  this — blueprint-first search is superseded.
- **Pool selection happens on the planner** (2026-11-20 decision of
  record): a Plan participants section (the corporation follows the
  main character set on the Roster — no planner-side selector; corp
  members default to all included with per-member toggles;
  other-corporation characters included per plan with the
  distribution step) sits between the target and the requirement
  tiers, set before Calculate — eligibility, allocation, and stock
  meters resolve against it. The build-plan header's picker is the
  what-if re-run control.
- Dashed yellow `.anno` boxes are wireframe annotations and would
  never ship.
- Data provenance is documented per set in that set's README:
  quantities, phases, and timelines from the matching chain document;
  blueprint ownership from the live `blueprints` table; material
  *availability* numbers may be invented for meter demos and are
  flagged there.

## Planned sets (2026-11-19)

The full mockup program runs **before milestone implementation** —
mockups surface milestone clarifications cheaply, so the design work
completes first. Two kinds of sets: **chain sets** (the binding
three-page convention above, only data changes) and **surface
mockups** (single new page types, proposed once against the reference
component set — the convention's new-component rule applies). The M3
structure manager surface is landed (`structures/`); the M15 sync
panel and M12 capability surface remain.

Order (chain sets by escalating complexity, then the surfaces — the
three surface mockups are independent and can slot anywhere):

**Skill gates are simulated as met from the Jackdaw set on**
(2026-11-19): the Panther set owns the missing-skills scenario (sole
inventor, out-of-corp, unresolvable-as-scoped), so the remaining sets
assume the roster holds the required skills and spend their surface
area validating the chain systems — the complex mechanics and their
edge cases, not the skill gate.

The **wave-progress bar** (added in the 2026-11-19 refinement pass) is
part of the standard chain-set pages from here on — every set's
build-plan pages carry it. A future set whose plan uses pipelining
should exercise its multi-row Gantt form (the serial bar is the
single-row case of that shape).

1. **Refinement pass** — `typhoon/` + `charon/` updated for the
   world-state sync band: contract availability backed by local
   synced tables (The Forge-only staged scope, sync freshness),
   hub/structure-source annotations, market-price context where the
   data now exists.
2. **Panther** — invention modeling: the invention input tier
   (source-BPC → invented-BPC), 22% base probability from the Typhoon
   Blueprint, expected-runs math, decryptor selection on the
   calculated plan (M8).
3. **Jackdaw** — T3: invention from three relic grades (26/21/14%,
   runs set by the grade), relics and Sleeper salvage as new
   terminator classes, the fullerene-polymer reaction world, invention
   over-delivery (one success = 20 ships' worth), and the
   drop-sourced BPC acquisition path. The earlier hull + subsystems
   multi-target bullet was corrected 2026-11-19 — tactical destroyers
   have no subsystems, and no hull consumes subsystems; multi-target
   is a possible future UI feature, not a chain mechanic.
4. **T2 rigs** (+ a high-volume consumable variant — ammo or
   drones): validates invention at medium and production volume, and
   that workflows aren't strictly ship-building.
5. **Reaction-terminal target** (advanced moon composite or booster)
   — the deliverable itself is a reaction product: validates the
   workflow isn't manufacturing-centric at the target level.
6. **Faction components** — the LP-store acquisition mechanic:
   faction commodities' BPCs are purchasable only from LP stores
   (faction ammo, faction-equivalent hulls like the Typhoon Fleet
   Issue — not invented), paid in loyalty points, a separate
   faction-typed currency earned through missions, faction warfare,
   and similar, transferable between characters, with no ISK market
   for the currency itself. Validates the fifth acquisition path
   (LP-earned BPCs) and the LP-balance/run-store surfaces — see the
   TODO investigation item for the data-layer gaps (no loyalty scope
   registered; LP store offers not in the SDE mirror).
7. **Supercarrier** — the supercapital tier, gentler half.
8. **Titan** — the absolute chain stress test (titan-class
   components on top of the capital set).
9. **M3 structure manager** — the facility-registry CRUD surface
   (activity, type, rigs, security, tax, defaults) that feeds M4's
   facility defaults.
10. **M15 sync panel** — sync_hubs management (The Forge seed, custom
   region hubs, structure hubs with the scope-prerequisite state),
   per-family sync status, rate-limit headroom with the
   staged-rollout gate visible.
11. **M12 capability surface** — "what should we build": ranked
    end-product recommendations + per-target gap report (the
    fork-point substrate M13/M14 consume).

Deferred by design: the M14 farming flow (node-marking → bid
request) — the marking mechanism already exists in the plan mockups;
design it when M14 approaches.

**M10's analysis surfaces: at-milestone design work, not mockup
sets** (evaluated and decided 2026-11-21): the chain sets already
carry M10's UI shapes in their honest pre-state — Purchase ⇄ Build
chips on every node, market-average figures on acquisition tables
(flagged illustrative), contract-match treatments, `.sync-source`
provenance lines, and the LP portfolio view (the TFI set). What's
missing is the *verdict logic* behind them — build-vs-buy decisions
are calculations over M15's synced prices, which don't exist in
local tables yet; mocking them now would invent both the data and
the analysis, front-running M10's recorded design decisions. The
mockup program's remaining market surfaces are the M15 sync panel
and the M12 capability surface (both structural — designable
without real prices), and the program completes with those plus
M3. M10's design happens at M10, against M15's real data.
