# Charon mockup set

The capital stress-test set — same pages, layout, and components as the
reference standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention), populated
with the Charon ×1 chain. It exercises everything the Typhoon set
couldn't: missing blueprints with contract backfill, capital components,
recurring commodities, mixed-activity phases, and the new terminator
classes (gas, tier-4 PI, molecular-forging tools).

| File | Shows |
|---|---|
| `planner.html` | Search (Missing chip on the Charon Blueprint), three-tier requirement overview at ×1, contract-availability view for the unowned blueprint, Calculate |
| `build-plan.html` | Freshly calculated plan: wave-progress bar, 6-phase reverse chain with recurring fuel blocks, capital components with BPC-via-contract badges, Cargo Bay flipped to Purchase (missing-blueprint alternative demo), required blueprints inverted (9 missing with backfill table), owned-BPO-only copy plan, gaps-only acquisition with the new categories, wave-1 job allocation |
| `build-plan-active.html` | The same plan mid-flight (day 12.4 of 21.7): wave-progress bar at 57% (legend expanded), phases 1–5 complete, the single 11.8-day ship build running at 21%, contract backfills all filled |

**2026-11-22 fan-out**: every page carries the standard 2026-11-22
conventions — the planner's Plan facilities and sell-side market
sections, the build plan's Market panel (build-vs-buy verdicts +
estimated profit) and wave pager, the active page's running market
readout with open verdicts — populated with this chain's data — the Charon active page demonstrates the fully-committed market state (tiles + realized ledger, no open verdicts). All Ƶ figures are illustrative
until M15's price sync; full section notes live on the Typhoon
reference set.

## Data provenance

- Quantities, phases, runs, job shapes, and the 21.7 d / 25.7 d chain
  ends come from `reference/chains/CHARON-CHAIN.md` (the model runs at
  ×1 against the live SDE mirror).
- Type IDs and names from the SDE mirror; icons against
  `images.evetech.net` (blueprint types use the bp/bpc render variants).
- Blueprint ownership from the live `blueprints` table, pulled
  2026-11-19: 41 blueprints in the chain — the Charon, all seven
  capital-component blueprints, and ten reaction formulas are genuinely
  missing (18); AIPS/LSBU/CTR, the fuel-block sets, and sixteen
  reaction formulas are genuinely owned (23).
- The Charon Blueprint contract listing is **real** (The Forge,
  2026-11-19: one contract, ten identical 1-run ME 10 / TE 20 BPCs,
  300M — the same-type-bundle corner case). The other contract rows,
  all material *availability* numbers, and the market-average figures
  on the acquisition table are **invented for the wireframe** — the
  real ones arrive from M15's world-state sync band (staged rollout:
  The Forge alone first; the ESI fields were verified live 2026-11-18).
- Character names, portraits, and structure names are the live roster
  and Amamake structures, as in the Typhoon set.
- The wave-progress bar's schedule decomposition (wave boundaries,
  durations, dead zones) is **illustrative** — anchored to the chain
  document's phase delivery days (components day 9.9, ship day 21.7)
  but invented in between; the real waves are the M9 scheduler's
  output.
