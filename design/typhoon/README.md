# Typhoon mockup set — the reference standard

Static wireframes for the build planner surfaces (M4–M6, M9) — the planner
entry page and the resulting build plan, including a mid-flight state
variant — populated with the Typhoon ×10 chain. This set is the
**reference standard** for the mockup convention (see
[`../README.md`](../README.md)): every chain gets these same pages,
layout, and components with only the data changed. These are design
artifacts for iteration, **not** app code: no build step, no JS, nothing
wired to the FastAPI app. They are deliberately kept out of `docs/` so
the Zensical site never publishes them (they contain live character and
corporation names).

## Viewing

Open the HTML files directly in a browser (`file://` works). Type icons and
portraits load from `images.evetech.net`, so icons need internet access;
everything else is self-contained.

| File | Shows |
|---|---|
| `planner.html` | Search + autocomplete (with icons, Owned badges), target count stepper, inputs overview, Match From Inventory, owned-copies overlay (BPO/BPC · location · ME/TE), Calculate |
| `build-plan.html` | Freshly calculated plan: wave-progress bar, reverse chain (phase strip + expandable tree, Purchase ⇄ Build chips, stage states), required blueprints, copy plan, raw-material meters, wave-1 job allocation |
| `build-plan-active.html` | The same plan mid-flight (day 1.6 of 9.5): wave-progress bar at 17%, stage states advanced, running jobs with time-to-delivery, next-up queues, ready-to-deliver slots, copy progress |

`mockups.css` holds the shared styles — design tokens and component shapes
copied from `app/static/style.css` (the styling source of truth), plus the
new components these mockups propose: `.meter`, `.stage-chip`,
`.stage-state`, `.activity-tag`, `.slot-grid`, `.chain-flow`,
`.autocomplete`, `.sync-source`, `.wave-bar`. Dashed yellow `.anno` boxes are wireframe annotations and
would never ship.

## Data provenance

Everything is real, pulled 2026-11-17 from the live dev database:

- Quantities, run counts, phases, and the copy pipeline derive from
  `reference/chains/TYPHOON-CHAIN.md` (Typhoon ×10 target: chain end 9.5 d, AIPS copy as
  critical path).
- Type IDs, blueprint names, and `maxProductionLimit` values come from the
  SDE mirror; icons use those IDs against `images.evetech.net`.
- Owned blueprints (the Typhoon BPC set, fuel-block BPCs/BPOs, reaction
  formulas), character names, and structure names come from the synced
  `blueprints` / `characters` / `universe_locations` tables.
- Material *availability* numbers are invented for the meter demo — the
  pool-measurement math is M5 scope. The market-average figures on the
  acquisition table are likewise illustrative; M15's price sync is the
  future source. The wave-progress bar's schedule decomposition (wave
  boundaries, durations, dead zones) is illustrative too — the real
  waves are the M9 scheduler's output.

## Iteration

Edit the HTML/CSS directly; refresh the browser. Settled design decisions
are recorded in `MILESTONES.md` ("Decisions already made"); anything still
open is flagged in `.anno` boxes on the pages and tracked in
`ITERATION.md`.

## Milestone mapping

| Mockup section | Milestone |
|---|---|
| Search + autocomplete, target count | M2 catalog surface / M4 planner entry |
| Inputs overview, owned-copies overlay | M4 + M5 blueprint-availability overlay |
| Reverse chain, phase tree, stage chips | M5 chain resolution & phase view |
| Raw-material meters | M5 acquisition table + M6 progress tracking |
| Copy plan | M9 copy & BPC planning |
| Job allocation, slots, next-up | M9 job orchestration (+ M6 job correlation) |
| Plan states (Draft / Active) | M6 build plans |
