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
| `build-plan.html` | Freshly calculated plan: 6-phase reverse chain with recurring fuel blocks, capital components with BPC-via-contract badges, Cargo Bay flipped to Purchase (missing-blueprint alternative demo), required blueprints inverted (9 missing with backfill table), owned-BPO-only copy plan, gaps-only acquisition with the new categories, wave-1 job allocation |
| `build-plan-active.html` | The same plan mid-flight (day 12.4 of 21.7): phases 1–5 complete, the single 11.8-day ship build running at 21%, contract backfills all filled |

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
  300M — the same-type-bundle corner case). The other contract rows and
  all material *availability* numbers are **invented for the wireframe**
  (the contracts sync is future scope; the ESI fields it will consume
  were verified live 2026-11-18).
- Character names, portraits, and structure names are the live roster
  and Amamake structures, as in the Typhoon set.
