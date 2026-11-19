# Design — build planner mockups

Per-chain wireframe sets under `design/<target>/` — one directory per
simulation target, matching the `reference/chains/<TARGET>-CHAIN.md`
document it visualizes. Shared styles and components live in
`design/shared/` so every set renders identically.

| Directory | Set |
|---|---|
| `typhoon/` | planner → build plan → active plan — the **reference standard** |
| `charon/` | planner → build plan → active plan (capital stress test) |

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
component set — the convention's new-component rule applies).

Order (chain sets by escalating complexity, then the surfaces — the
three surface mockups are independent and can slot anywhere):

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
3. **Jackdaw** — T3: invention from three relic grades, relics as a
   new terminator class, and the multi-target plan (hull +
   subsystems as one target set — the first multi-target mockup).
4. **T2 rigs** (+ a high-volume consumable variant — ammo or
   drones): validates invention at medium and production volume, and
   that workflows aren't strictly ship-building.
5. **Reaction-terminal target** (advanced moon composite or booster)
   — the deliverable itself is a reaction product: validates the
   workflow isn't manufacturing-centric at the target level.
6. **Supercarrier** — the supercapital tier, gentler half.
7. **Titan** — the absolute chain stress test (titan-class
   components on top of the capital set).
8. **M3 structure manager** — the facility-registry CRUD surface
   (activity, type, rigs, security, tax, defaults) that feeds M4's
   facility defaults.
9. **M15 sync panel** — sync_hubs management (The Forge seed, custom
   region hubs, structure hubs with the scope-prerequisite state),
   per-family sync status, rate-limit headroom with the
   staged-rollout gate visible.
10. **M12 capability surface** — "what should we build": ranked
    end-product recommendations + per-target gap report (the
    fork-point substrate M13/M14 consume).

Deferred by design: the M14 farming flow (node-marking → bid
request) — the marking mechanism already exists in the plan mockups;
design it when M14 approaches.
