# Typhoon Fleet Issue mockup set

The faction set — same pages, layout, and components as the
reference standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention),
populated with the Typhoon Fleet Issue ×10 chain. It exercises what
no previous set could: the **LP acquisition layer** (the fifth
blueprint path — currency-gated, not ISK-gated), the **offer-variant
selection** as the planner's computed-choice card (the
decryptor/grade/cascade/throughput analog), the **wrong-currency
portfolio** rendered as visible-but-unusable wealth, the **earn-side
front owning the wave bar** (83% of the plan is a filling dead
zone), the **fourth distinct absent-copy cause** (the BPCs are the
purchase), and a build world that is **fully green** — no simulated
skills, no missing blueprints, no zero-stock inputs beyond the
familiar mineral mountain.

| File | Shows |
|---|---|
| `planner.html` | Commodity-first search (the TFI beside its T1 parent, differing only in acquisition path), Plan participants (completely green skill surface — a program first; LP balances ride as pool data), 4-type blueprint tier (3 owned, 1 LP), intermediates and raw summaries, the **offer-variant card** (every way to buy ten BPCs — TLF 10-pack at 20k LP each vs singles vs navy, against live balances per corporation) |
| `build-plan.html` | The acquisition-front-dominated wave bar (83% LP front · 7% components · 10% hulls), the currency-gated target node (a new gating reason with earn/distribute/switch-store remediations), the **LP acquisition plan** (per-source balances, paths, lead times — the curated corp balance and the distribution workflow), the fourth absent-copy state, gaps-only mineral mountain, the build world's ready-state allocation |
| `build-plan-active.html` | Day 12 of 21 (57%): the **LP front filling** (104k of 200k across two FW farmers — a dead zone with its own progress meter), the build world delivered early and waiting (components built day 3–4 inside the front), the **LP ledger** (earners, rates, target line, and the wrong-currency rows persisting as the portfolio view), hull wave queued on the purchase |

## Data provenance

- Quantities, phases, and the build world come from
  `reference/chains/TFI-CHAIN.md` (the model runs at ×10 against the
  live SDE mirror, release 2026-11-20). Component bills (AIPS 667
  runs · LSBU 334 · CTR 10), the reaction stack, and Industry-1
  gating are SDE data.
- Offers from the fuzzwork lpstore dataset (live-pulled 2026-11-21):
  the four TLF variants and the navy 500–600k comparison are real
  offer rows; the **runs-per-BPC = 1** assumption is the recorded
  pin (community convention — verify at purchase).
- LP balances from the live character loyalty read (2026-11-21,
  post-re-auth): TLF 0, Republic Fleet 8.5k, Paragon ~632k — all
  real. The corporate militia balance is the curated entry
  (owner-maintained against the in-game wallet). Blueprint
  ownership real: the three component BP families owned with the
  formula set; mineral stock real (Tritanium 122% covered,
  Pyerite 2%).
- **No skill simulation anywhere** — Industry 1 minimum, held at 5
  across the roster; the first set since the Typhoon with a
  completely green skill surface, on a fully owned build world.
- Wave decomposition (the 21-day chain end, the earn front's
  dominance, the day-17.5 purchase), earn rates (~12k LP/day
  combined — gameplay parameters the planner carries, not
  computes), intermediates movements, and market figures are
  **invented for the wireframe** — illustrative, anchored to the
  chain document's durations.
