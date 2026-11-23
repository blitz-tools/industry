# Jackdaw mockup set

The T3 set — same pages, layout, and components as the reference
standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention), populated
with the Jackdaw ×1 chain. It exercises what no previous set could:
**relic-based invention** (the relic item itself carries activity 8 —
no source blueprint; three grades setting both probability and BPC
runs), the **grade choice as a price-only decision** (no decryptor
axes), **invention over-delivery** (one Intact success = 20 ships'
worth against a ×1 target), the **fourth blueprint acquisition path**
(drop-sourced BPCs — 1000-run site-drop copies), the **absent copy
plan** (the M9 surface edge case), the **inverse-Charon wave shape**
(the 50 h ship build owns 80% of the bar), and a raw story dominated
by **zero-stock w-space procurement** (15 Sleeper salvage types + 9
fullerites). Three pages, not four: per the 2026-11-19 simulation
convention, skill gates are simulated as met — the Panther set owns
the missing-skills scenario.

| File | Shows |
|---|---|
| `planner.html` | Search (relic family + grade probabilities in the autocomplete sub-line — no source blueprint), target with the T3 invention-inputs tier (three relic grades with p and runs-per-success, datacores vs stock, the no-decryptor note), 23-blueprint tier across four acquisition paths, intermediates and raw summaries (24 types at zero), invention-summary card (grade table, E[attempts], over-delivery, price-only grade choice), Calculate |
| `build-plan.html` | Freshly calculated plan: the inverse-Charon wave bar (W1–W3 inside the first 20%, W4 ship build at 80%), 4-phase chain with the mixed-activity polymer phase, invention plan (5 Intact attempts · 78% · one 1 h window · no job-lock · out-of-corp distribution step), required blueprints across four paths, the absent copy plan, gaps-only acquisition led by sleeper salvage and fullerites, wave-1 allocation with blitzrage's five invention slots |
| `build-plan-active.html` | The same plan mid-flight (day 1.8 of 2.5, 72%): invention complete at 2/5 successes (E = 1.3) with the over-delivery realized (40-run BPC, 1 used), reactions and components delivered inside day 0.5, ship build running at 62% on Octavia |

**2026-11-22 fan-out**: every page carries the standard 2026-11-22
conventions — the planner's Plan facilities and sell-side market
sections, the build plan's Market panel (build-vs-buy verdicts +
estimated profit) and wave pager, the active page's running market
readout with open verdicts — populated with this chain's data. All Ƶ figures are illustrative
until M15's price sync; full section notes live on the Typhoon
reference set.

## Data provenance

- Quantities, phases, runs, and the invention layer come from
  `reference/chains/JACKDAW-CHAIN.md` (the model runs at ×1 against
  the live SDE mirror). Relic grades (26/21/14% at 20/10/3 runs per
  success), the shared recipe (3 + 3 datacores, 1 h attempts), and
  durations (10-minute components, 3-hour reactions, 50 h build) are
  SDE data; the no-decryptor / fixed-ME-per-grade behavior is the
  community-documented M8 pin.
- Blueprint ownership from the live `blueprints` table, pulled
  2026-11-19: 23 blueprints — 21 owned (8 component BPs as
  **1000-run ME 10 / TE 20 drop-sourced BPCs**, 9 polymer formulas and
  fuel blocks as originals) and 2 genuinely missing (the invented
  Jackdaw Blueprint, the NPC-seeded R.A.M. BPO). Relic stock (0) and
  datacore stock (12 + 97) are real; so is the zero-stock T3 raw
  world (all 15 salvage types, all 9 fullerites, three isotope types)
  and the mineral mountain that dwarfs this bill (97.4M Tritanium
  against 2,556 needed).
- **Skills are simulated** per the 2026-11-19 program convention:
  live, nobody on the roster holds Sleeper Encryption Methods
  (blitzrage is nearest — both sciences at 4, the encryption skill
  untrained), and nobody holds the build gate (Advanced Small Ship
  Construction 5; Octavia tops out at 4). The mockups feature
  blitzrage as inventor and Octavia as builder with the gaps assumed
  trained. Corp membership is real: blitzrage is out-of-corp, so the
  invention inputs carry the distribution step.
- Wave decomposition (W1 1 h invention + fuel blocks … W4 50 h ship
  build), the 2.5 d chain end, material *availability* movements, and
  market-average figures are **invented for the wireframe** — anchored
  to the chain document's durations but illustrative in between; the
  real waves are the M9 scheduler's output.
