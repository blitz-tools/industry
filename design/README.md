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
| `markets/` | single surface page — the M15 sync panel: the market manager (hubs disableable, custom/player CRUD) + sync families + the rate-limit headroom gate |

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
- **Facility selection happens on the planner** (2026-11-22 decision
  of record): a Plan facilities section follows Plan participants —
  one selector per activity (manufacturing / copying / invention /
  reactions), pre-selected on the Structures registry default,
  plan-scoped overrides. Copying is its own selector defaulting to
  the invention facility's default (copy jobs may run elsewhere and
  the BPCs travel). A **sell-side market** selector follows: trade
  hubs plus player markets from the market manager (M15), setting
  the estimated sell price and profit readout. Landed on the
  Typhoon reference set and fanned out to every set (2026-11-22).
- **Build-plan pages carry a Market panel** (2026-11-22): the
  Purchase ⇄ Build chips roll up into per-commodity build-vs-buy
  verdicts at the selected market, with plan totals and estimated
  profit; active plans run the readout (cleared input cost, sell
  price re-checked at wave boundaries, negative profits render
  pink). Figures illustrative until M15's price sync; verdict
  arithmetic is M10's.
- **Currency displays as Ƶ** (2026-11-22): U+01B5 replaces "isk" as
  the currency symbol globally, and money totals read
  `<total> Ƶ (<per-item> Ƶ)` — total first, per-item in parens.
- **No scenario-composed sentences** (2026-11-22, extending the
  no-editorial-prose decision to every surface): UI text is static
  scaffolding with computed values in slots — state badges,
  structured fields, table rows; a sentence whose structure would
  change per scenario decomposes into badge + fields + static help,
  with remediations as links. Fixed-template sentences with value
  slots are fine. Reference implementation: the markets page's
  headroom gate; the 2026-11-22 sweep normalized the active market
  readouts and settled lines across all sets.
- **Job allocation pages through waves** (2026-11-22): a `‹ Wave ## ›`
  pager on the job-allocation section — the current wave is always
  the default view until it completes; paging left shows historical
  waves, paging right shows future waves at their current readiness.
  A future-wave job whose inputs arrived early renders eligible with
  an **Early start** control (per-job, owner-chosen, never
  automatic); taken early starts show as pre-started, running inside
  the future wave and counted in the plan. This is pipelining's UI
  preview — the scheduler stays serial until the M9 pipelining
  decision. Landed on the Typhoon reference set and fanned out to
  every set (2026-11-22).
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
structure manager (`structures/`) and M15 sync panel (`markets/`)
surfaces are landed; the M12 capability surface remains.

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
sets** (evaluated 2026-11-21; **revised 2026-11-22**): the chain sets
carry M10's UI shapes — Purchase ⇄ Build chips on every node,
market-average figures on acquisition tables (flagged illustrative),
contract-match treatments, `.sync-source` provenance lines, the LP
portfolio view (the TFI set), and now the **Market panel** on the
build-plan pages (Typhoon reference set first): per-commodity
build-vs-buy verdicts, plan totals, and the estimated-profit
readout, with illustrative figures. The 2026-11-21 evaluation held
that mocking verdicts would front-run M10's design decisions; the
2026-11-22 product direction supersedes it for the *panel shape* —
mocked now, clearly flagged — while the *verdict logic* still lands
at M10, against M15's real synced prices. The mockup program's
remaining market surfaces are the M15 sync panel (the market
manager) and the M12 capability surface (both structural —
designable without real prices). M10's analysis design happens at
M10, against M15's real data.
