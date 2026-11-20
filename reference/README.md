# Reference — planner proof-out scripts

Symbols and model terms (T_in, t_c, t_b, …) stay unexpanded in these
documents by design — look them up in [`GLOSSARY.md`](GLOSSARY.md), the
maintained math reference. Keep it updated when new terms enter.

Executable spec for the industry planner's calculation core. These scripts
regenerate the golden values in `reference/chains/TYPHOON-CHAIN.md` and
encode the algorithms the milestones graduate into the app: chain
expansion → M5, time/job math → M4, scheduling and copy strategy → M9,
BPO (Blueprint Original) recommendations → M12. They are reference
implementations, not app
code — no ORM, no framework, stdlib only, read-only against the database.

Run inside the dev container from the repo root:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 644 1
podman exec industry_dev_1 python reference/timeline_model.py 644 100
podman exec industry_dev_1 python reference/timeline_model.py 644 100 \
    --timelines 10,25,50,100
podman exec industry_dev_1 python reference/timeline_model.py 644 100 --bpo
podman exec industry_dev_1 python reference/timeline_model.py 644 100 --horizon
```

`--char <character_id>` runs the model with that character's computed skill
multiplier instead of the max-skills scenario; `--corp <id>` picks the pool.

## Chain documents (`reference/chains/`)

Per-chain golden-value documents, one file per simulation target:
`<TARGET>-CHAIN.md`. `TYPHOON-CHAIN.md` (Typhoon, the standing M5
validation case) is the template — full chain expansion, aggregated
phases, raw-material acquisition table, scheduling model, timelines,
and scaling analysis, all generated from the scripts above.
`CHARON-CHAIN.md` (Charon freighter, 2026-11-18) is the capital
stress test: seven-deep phases, recurring commodities, mixed-activity
phases, and four terminator classes the Typhoon never exercised.
`PANTHER-CHAIN.md` (Panther T2 battleship, 2026-11-19) is the
invention stress test: the invention layer (22% base from the Typhoon
Blueprint, datacores, decryptor scenarios pinned from live ESI dogma),
the T1 hull riding inside the chain as a build input, capital-component
crossover (Capital Jump Drives), T2 components at 1/run volumes
(18,750-run armor-plate jobs), and the NPC-seeded T2 component BPO
(Blueprint Original) acquisition path.
`JACKDAW-CHAIN.md` (Jackdaw T3 tactical destroyer, 2026-11-19) is the
reverse-engineering stress test: relic-based invention (the relic item
itself carries activity 8 — no source blueprint; three grades setting
both probability and BPC runs, 26/21/14% at 20/10/3 runs), the
multi-product recipe shape (all four racial tactical destroyers per
relic), no decryptors and no job-lock, two new terminator classes
(relics, Sleeper salvage), polymer reactions consuming minerals
directly, invention over-delivery (one success = 20 ships' worth), and
the drop-sourced BPC acquisition path (1000-run component copies).
`TRIMARK-CHAIN.md` (Large Trimark Armor Pump II T2 rig, 2026-11-20) is
the medium-volume invention and first non-ship stress test: ten
invention successes at 34% (binomial planning to a confidence target),
maxProductionLimit 1 manufacturing (every unit its own job — volume
scales job count), the wreck-salvage terminator class with T1/T2
condition tiers, and the copy plan pre-satisfied by inventory (the
corporation's live T1 Trimark copy operation). `RAGE-CHAIN.md`
(Scourge Rage T2 heavy assault missile, 2026-11-20) is the
production-volume consumable: 5,000 missiles per run against a 98-run
owned BPC pool (the run-pool top-up edge), alternative-product
invention (Javelin siblings on the same recipe), deterministic
reaction-batch over-delivery, two reaction tiers beneath a non-ship
deliverable, and the live-BPC reconciliation that puts the
invented-base ME/TE pin at 2/4 (Attainment + base reproduces the
owned 14-run ME 1 / TE 8 BPCs exactly).

New chains are added to stress the models with more complex structures
(deeper phase stacks, capital components, invention/T2 layers) and
surface assumptions that break — every "known simplification" below is
a candidate for exactly that. When a chain exposes a bad assumption,
record it in the chain document and the fix in this README's model
notes; the milestone text records what changes for the app.

## Formula reference

Everything is closed-form arithmetic over the SDE (Static Data Export)
mirror (`sde_*` tables)
plus the synced `skills`/`blueprints`/`characters` tables. No LLM at
runtime; nothing here is learned or guessed at run time.

**Chain expansion (M5)**

- producing blueprint: first `industryActivityProducts` row for the type
  (manufacturing = activity 1, copying = 5, reactions = 11 — `ramActivities`
  labels reactions 9, but the data lives on 11)
- runs = ⌈units ÷ products-per-run⌉ (`industryActivityProducts.quantity`:
  components 3/run, fuel blocks 40/run)
- phases: level-by-level aggregation; same-type requirements merge per
  phase, then round runs once — not per parent (the material savings:
  RCF (Reinforced Carbon Fiber) 8 per-branch runs → 7 aggregated)
- terminators: types with no producing blueprint (minerals, moon
  materials, PI (Planetary Industry) commodities, ice products, gas
  from harvestable clouds, NPC-seeded market goods, Sleeper salvage) —
  leaves to acquire, never recursed; raw categories are hardcoded
  here, M5 classifies via invGroups/invCategories — validated against
  the Charon chain (2026-11-18): the SDE groups map cleanly except
  molecular-forging tools ('Commodities' catch-all), which need a
  name-list fallback; the Panther chain (2026-11-19) added Morphite
  (SDE files it under 'Mineral' despite being the top moon material)
  and Construction Blocks (no blueprint exists — NPC-seeded); the
  Jackdaw chain (2026-11-19) added the Sleeper salvage ('Ancient
  Salvage' group, maps cleanly) and a second walk-invisible
  terminator class, the invention relics themselves (*Ancient
  Relics* category — they enter only through the invention overlay);
  the Trimark II chain (2026-11-20) added the wreck salvage
  ('Salvaged Materials' group, 41 types, maps cleanly — T1 rigs eat
  the damaged variants, T2 the intact ones); the Rage chain
  (2026-11-20) added Rocket Fuel (no blueprint exists — NPC-seeded,
  like Construction Blocks)
- invention (activity 8) is an overlay, never a walk step: the
  invented blueprint's build inputs resolve through the normal walk,
  and the invention recipe (source BPC, probability, datacores,
  skills, T1 runs consumed per attempt — implicit in the game, absent
  from the SDE materials) reports as its own layer with
  expected-value math (attempts = 1/p, confidence 1−(1−p)ⁿ) and a
  decryptor scenario table. T2 plans also model their **copy layer**
  (2026-11-20 direction, Trimark II / Rage chains): invention inputs
  are copied from BPOs rather than assumed — BPC count is the
  invention-parallelism knob (one active job per blueprint), copy
  time is split-invariant across run-count choices, so the sizing
  rule is BPC count = min(attempt budget, invention slot pool) with
  runs per BPC = ⌈budget ÷ count⌉; the copy phase is BPO-bound and
  can own the wall-clock (Trimark: 18 h copy vs 6.5 h invention at
  full parallelism). Owned source-BPC runs remain an availability
  overlay that can zero the phase. The copy phase has two consumption
  **destinations** — Copy → Invention (mandatory: invention consumes
  BPC runs, one per attempt, budget = confidence-targeted attempts)
  and Copy → Manufacturing (optional: the copy-vs-direct economics of
  the Typhoon analysis, deterministic run-need) — which coexist in
  one copy wave when an invention source's T1 product is also a build
  input (the Panther's Typhoon BPC pool); see MILESTONES.md's
  copy-destinations entry. Expected quantities stay OUT of the
  deterministic raw-material table — probabilistic inputs present as
  expected + confidence (the M8 decision). Decryptor modifiers are
  pinned from live ESI dogma (2026-11-19) in `DECRYPTORS` — the dogma
  tables are not part of the SDE mirror; invented-BPC base ME
  (Material Efficiency)/TE (Time Efficiency) is NOT in SDE/ESI — the
  −4/−4 community value is now challenged by live evidence (Rage
  chain, 2026-11-20: base 2/4 + Attainment reproduces the owned
  14-run ME 1 / TE 8 BPCs exactly; the owned rig BPCs at 2 runs /
  0 / 0 match no row) — pin at M8. BPC runs per success is the
  activity-8 product quantity (1 for ships and rigs, 10 for T2
  ammo); owned BPCs always render their ESI-synced values and only
  projections use the SDE quantity. The overlay dispatches on the
  probability rows for the product blueprint: one row renders the T2
  recipe — which may carry **alternative products** (Rage chain,
  2026-11-20: the same source recipe holds the Javelin BPC's
  probability row too — sibling rolls, not the T3 grade mechanism;
  by-product-or-miss semantics pin at M8); multiple rows render the
  **T3 relic grades** (Jackdaw chain, 2026-11-19) — the relic item
  itself carries activity 8 (no source blueprint), the grade sets
  both probability and BPC runs per success (the activity-8 product
  quantity, 20/10/3 for small hull sections), recipes are
  multi-product (all four racial tactical destroyers per relic — the
  job targets one output), and there is no job-lock (each attempt
  consumes its relic). T3 BPC ME/TE is fixed per grade and decryptors
  do not apply — both community-documented, pin at M8
- cycle detection: NOT implemented (T1 manufacturing has none); M5 must
  add it defensively

**Time and job math (M4, M9)**

- per-run times from `industryActivity` (seconds → hours)
- manufacturing time × per-character skill multiplier — **computed from the
  synced `skills` table, never a global constant** (the 0.68 in the
  proof-outs is the max-skills scenario; the roster already diverges —
  theblitzrage holds Advanced Industry 1 → 0.776). The skill→effect mapping
  itself (`MFG_SKILL_MAPPING`) is UNVERIFIED pending the dogma check
- job sizing: k = min(maxProductionLimit, ⌈runs ÷ pool⌉); jobs = ⌈runs ÷ k⌉;
  even split (all jobs end together within one run)
- blueprint job-lock: one active job per blueprint — concurrency per
  commodity = min(slot pool, blueprint count); reactions at 1 BPO per
  character per formula → roster-size concurrency; copying at 1 job per BPO
- login windows: job durations reported in 6h windows (plan parameter)

**Scheduling (M9)**

- serial phases, deepest first; each phase starts at max(previous phase
  end, its commodities' copy-queue ends); the gap is the dead zone
- phase duration = max(longest job, total slot-hours ÷ pool)
- strategies: pure copy; hybrid (copy the longest queue until inputs
  arrive, then build direct — applies when skilled build time < copy time
  per run; break-even multiplier = copy-time ÷ base-build-time, 0.8 across
  this chain); 2×BPO (second BPO for the longest queue)
- copy-vs-direct decision rule and the diminishing-returns analysis:
  see reference/chains/TYPHOON-CHAIN.md

**BPO recommendations (M12)**

- per commodity: queue rate (copy hours per target unit), input-ready rate
  (the next deeper phase's end, fitted linearly — scale-invariant)
- min BPOs = ⌈queue rate ÷ input-ready rate⌉ — the count that fits the
  copy queue into the input dead zone
- slot ceiling = ⌈pool × copy-time ÷ build-time⌉ — BPOs past which BPCs (Blueprint Copies)
  arrive faster than slots can build
- the acquisition ladder (un-gate one resource, the next surfaces) is
  manual analysis in `reference/chains/TYPHOON-CHAIN.md`; automating
  the iteration is M12 work

## Status and caveats

- Golden values: `chain_expand.py 644 1` and `timeline_model.py 644 100`
  reproduce reference/chains/TYPHOON-CHAIN.md's tables; small-N timeline values differ
  slightly from the doc's charts (the doc used linear-rate approximation,
  the script computes directly — the script is the source of truth).
- Unverified inputs (M4's dogma task): skill→time/copy multipliers,
  whether copying is skill-reducible, reaction slot semantics, exact
  BPO job-lock behavior. Invention pins (M8's dogma task, surfaced by
  the Panther chain): invented-BPC base ME/TE (−4/−4 assumed — live
  evidence from the Rage chain 2026-11-20 points to 2/4: base +
  Attainment reproduces the owned ammo BPCs' 14 runs / ME 1 / TE 8
  exactly, while the owned rig BPCs at 2 runs / ME 0 / TE 0 match no
  decryptor row from any candidate base), whether skill levels modify
  invention probability (assumed not, post-Crius), and
  alternative-product semantics (T2 ammo recipes carry sibling BPCs
  at their own probabilities — by-product or miss, and whether both
  can land on one attempt). T3 pins (surfaced by the Jackdaw chain):
  relic-grade BPC ME/TE values, decryptor non-applicability to
  reverse engineering, and the drop-sourcing of hybrid tech
  component BPCs (no producer, no invention recipe, no NPC seeding
  per community docs — verify against M15 market data). Rocket
  Fuel's NPC seeding (Rage chain) verifies against M15 too.
- Known simplifications: serial phases (no pipelining — parked open
  question in MILESTONES.md), one skill multiplier per model run (real
  assignments weight per character), facilities/rigs not yet multiplied
  (M3 data), market pricing absent (M10).
