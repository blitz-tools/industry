# Trimark mockup set

The T2 rig set — same pages, layout, and components as the reference
standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention), populated
with the Large Trimark Armor Pump II ×10 chain. It exercises what no
previous set could: **invention at medium volume** (ten successes at
34% — the program's first multi-success binomial plan), the **retry
loop** (staged batches, a shortfall realized, batch 2 re-armed with
cause — the 2026-11-20 retry-semantics direction, rendered by the new
`.loop-state` card), **maxProductionLimit 1 manufacturing** (every rig
its own 12.5 h job; concurrency = invention successes), the **copy
layer modeled from zero** (BPC count as the invention-parallelism
knob, the BPO-bound copy phase owning the wall-clock), the **wreck
salvage terminator class** (intact tier, all three types at zero), and
the smallest acquisition surface in the program (8 raw types).

| File | Shows |
|---|---|
| `planner.html` | Commodity-first search and target (the rig, not its blueprint), invention-inputs tier (corp 130-run source pool, datacore gap, simulated-skills note), 3-blueprint tier (invent · corp-owned source · NPC-seeded R.A.M.), intermediates and raw summaries (salvage stack at zero), invention-summary card (binomial confidence table, decryptor scenarios with the no-runs-payoff note), Calculate |
| `build-plan.html` | Freshly calculated plan: copy plan (30 one-run BPCs, sizing rationale), invention plan (batch 1 at 30 attempts / E 10.2 / 60% + the conditional re-arm row), no-dead-zone wave bar (copy 15 h → invention 6.5 h → ten 12.5 h builds, 1.4 d), 3-phase chain, required blueprints (1 to acquire), gaps-only acquisition (salvage + Isogen), wave-1 allocation (copy pairs rolling on 2 corp BPOs) |
| `build-plan-active.html` | The same plan mid-flight (day 1.2 of 1.9, 65%) with the **shortfall branch realized**: batch 1 complete at 8/10 (E was 10.2), the loop-state card (successes/attempt-budget meters, re-arm with cause, both residue directions held), re-arm copy wave + batch 2 running at 48%, build phase gated, material residue visible |

## Data provenance

- Quantities, phases, runs, and the invention layer come from
  `reference/chains/TRIMARK-CHAIN.md` (the model runs at ×10 against
  the live SDE mirror). Probability (34%), the recipe (3 + 3
  datacores, 6.5 h attempts, 1 run per success), maxProductionLimit 1,
  and the salvage bill (Interface Circuit 230 · Intact Armor Plates
  200 · Nanite Compound 150) are SDE data; the copy-sizing rule and
  retry semantics are the 2026-11-20 product directions recorded in
  MILESTONES.md.
- Blueprint ownership from the live `blueprints` table, pulled
  2026-11-20: 2 of 3 owned (the corporation's two Large Trimark I
  BPOs at ME 10 / TE 20 plus a 130-run BPC pool — the live copy
  operation), 1 missing (the NPC-seeded R.A.M. BPO). Datacore stock
  (21 + 30 against ≈88 + 88 expected), zero intact-salvage stock, and
  Isogen 0 are real; so is the 97.4M Tritanium mountain against a 556
  bill.
- **Skills simulated only where genuinely missing**: Amarr Encryption
  Methods (nobody holds it — the sole live gap). Both invention
  sciences are genuinely held (blitzrage 4), and the Armor Rigging 3
  build gate is genuinely held by three characters (blitzrage 4,
  theblitzrage 4, Storm Ragez 3).
- Wave decomposition (the two-batch invention plan, the re-arm
  branch's inserted waves, the 1.4 d expected / 1.9 d realized chain
  end), material *availability* movements, and market-average figures
  are **invented for the wireframe** — anchored to the chain
  document's durations but illustrative in between; the real waves are
  the M9 scheduler's output.
