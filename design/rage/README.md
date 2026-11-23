# Rage mockup set

The T2 ammo set — same pages, layout, and components as the reference
standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention), populated
with the Scourge Rage HAM ×500,000 chain. It exercises what no
previous set could: **production volume** (5,000 missiles per run, the
first target whose unit count outruns its run count by three orders
of magnitude), the **run-pool top-up** (98 owned runs of 100 needed —
one success fills the gap and over-delivers 8), **alternative-product
invention** (Javelin siblings on the same recipe; the by-product
realized on the active page), **residue as first-class inventory**
(the new `.residue-card` — banked BPCs, spare runs, deterministic
reaction over-delivery), **BPC job-lock on the wall-clock** (15 ammo
jobs in two rounds on 8 BPCs), and the **shopping-list acquisition
story** (9 formulas + 2 BPOs + an R8/R64 moon stack, nothing to mine
or farm).

| File | Shows |
|---|---|
| `planner.html` | Commodity-first search and target (the missile, not its blueprint — the target stepper at 500,000 with the 100-run derivation), invention-inputs tier (the 98/100 run-pool meter, T1 copy pool, datacores at exactly-4, sibling-product note, all-skills-held note), 15-entry blueprint tier (the live line · corp holdings · 11 missing), intermediates summary (two reaction tiers, batch over-delivery, fuel-block stock collapse), raw summaries (R4 covered / R8-R64 zero), top-up summary card (attempts-to-confidence with expected Javelin by-products), Calculate |
| `build-plan.html` | Freshly calculated plan: 5-wave bar (reactions → invention parallel branch → GPG → two BPC-bound ammo rounds, 2.7 d), 5-phase chain with per-node batch over-delivery, copy plan (4 one-run BPCs, 32 min), top-up invention plan (4 attempts · 81% · expected residue preview), required blueprints (11 to acquire, all NPC-seeded), gaps-only acquisition (moon stack + Rocket Fuel + Morphite), wave-1 allocation across the Reactions-5 holders |
| `build-plan-active.html` | The same plan mid-flight (day 1.5 of 2.7, 55%) with the **over-delivery realized**: top-up complete at 1 Rage + 1 Javelin success (the sibling by-product banked), GPG delivered, ammo round 1 running at 65% with the 2-run top-up job riding the invented BPC, the residue card (Javelin BPC · 8 spare runs · reaction surpluses), delivered-units meter at 0 with 350,000 in flight |

**2026-11-22 fan-out**: every page carries the standard 2026-11-22
conventions — the planner's Plan facilities and sell-side market
sections, the build plan's Market panel (build-vs-buy verdicts +
estimated profit) and wave pager, the active page's running market
readout with open verdicts — populated with this chain's data — **the negative-profit case**: at these prices the missiles buy cheaper than the plan builds them (the pink tile is the shape working; a stock or foundry decision, not arbitrage). All Ƶ figures are illustrative
until M15's price sync; full section notes live on the Typhoon
reference set.

## Data provenance

- Quantities, phases, runs, and the invention layer come from
  `reference/chains/RAGE-CHAIN.md` (the model runs at ×500,000 against
  the live SDE mirror). Probability (34% per product), runs per
  success (10), 5,000 missiles per run, reaction batches and their
  over-delivery, and durations (12.67 h attempts, 2.67 h/run
  manufacturing, 3 h reactions) are SDE data; the run-pool, residue,
  and retry semantics are the 2026-11-20 product directions recorded
  in MILESTONES.md.
- Blueprint ownership from the live `blueprints` table, pulled
  2026-11-20: the live T2 line (7 Rage BPCs at 14 runs / ME 1 / TE 8,
  the T1 original + 3 copies totaling 586 runs), the corp's Sulfuric
  Acid formula (1 of 10 needed), and the fuel-block holdings; 11
  missing, all NPC-seeded originals. The 98-run pool, datacore stock
  (29 + 4), 7,975 Rage / 8,595 Javelin missiles held, the R4 moon
  surplus (Evaporite 43k), and the zero-stock R8/R64 stack are real.
- **No skill simulation anywhere** — the first set since the Typhoon
  whose every gate is held live (blitzrage: Caldari Encryption 1,
  Electronic Engineering 1, Rocket Science 1, Graviton Physics 4,
  Reactions 5; four characters at Reactions 5; Industry 5 across the
  roster).
- Wave decomposition (the 2.7 d chain end, round boundaries), the
  realized invention outcome (1 + 1 against E 1.4 each), material
  *availability* movements, and market-average figures are **invented
  for the wireframe** — anchored to the chain document's durations
  but illustrative in between; the real waves are the M9 scheduler's
  output.
