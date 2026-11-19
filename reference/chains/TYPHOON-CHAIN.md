# The Typhoon chain — full reference

The completely expanded production chain for the **Typhoon** (T1
battleship, type 644, blueprint 998) at target quantity ×1 — the
worked example M5's chain resolution gets checked against — plus the
×100 work-distribution models that M9's job assignment gets checked
against (v1: slot-spread; v2: time-balanced with copy/reaction BPO (Blueprint Original)
constraints, target-count timelines, and BPO obtainment
recommendations). This file exists because the full expansions are
too heavy for `MILESTONES.md` or `TODO.md`, but the detail matters:
batch sizes, per-run product quantities, shared intermediates, the
raw-material totals, and the slot-distribution shape all inform the
resolver's and assignment engine's design.

Provenance: read directly from the live SDE (Static Data Export) mirror (`sde_*` tables,
release 2026-11-13) on 2026-11-16. Expansion rule: for each required
type, find its producing blueprint (manufacturing = activity 1,
reactions = activity 11), compute runs = ⌈needed ÷ product-per-run⌉,
multiply inputs by runs, recurse; types with no producing blueprint
are `[raw]` terminators. Re-run the same queries after each SDE
release if the numbers drift.

Conventions: `x<N>` is the quantity required at that node (already
multiplied up to the target count); `(N runs, P/run)` is the run
count with the recipe's product-per-run; `[raw]` marks a
non-buildable terminator.

## Per-branch tree (Typhoon ×1)

The recipe view — every branch shown, shared intermediates repeated
under each parent. 177 nodes.

```text
- Typhoon x1 [manufacturing] (1 run)
  - Core Temperature Regulator x1 [manufacturing] (1 run)
    - Chiral Structures x100  [raw]
    - Water x100  [raw]
    - Pressurized Oxidizers x500 [reaction] (3 runs, 200/run)
      - Carbon Polymers x600 [reaction] (3 runs, 200/run)
        - Helium Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Hydrocarbons x300  [raw]
        - Silicates x300  [raw]
      - Sulfuric Acid x600 [reaction] (3 runs, 200/run)
        - Nitrogen Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Atmospheric Gases x300  [raw]
        - Evaporite Deposits x300  [raw]
      - Oxy-Organic Solvents x3 [reaction] (1 run, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x2,000  [raw]
        - Atmospheric Gases x2,000  [raw]
    - Reinforced Carbon Fiber x500 [reaction] (3 runs, 200/run)
      - Carbon Fiber x600 [reaction] (3 runs, 200/run)
        - Hydrogen Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x300  [raw]
        - Evaporite Deposits x300  [raw]
      - Oxy-Organic Solvents x3 [reaction] (1 run, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x2,000  [raw]
        - Atmospheric Gases x2,000  [raw]
      - Thermosetting Polymer x600 [reaction] (3 runs, 200/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x300  [raw]
        - Silicates x300  [raw]
  - Life Support Backup Unit x75 [manufacturing] (25 runs, 3/run)
    - Test Cultures x200  [raw]
    - Viral Agent x200  [raw]
    - Reinforced Carbon Fiber x250 [reaction] (2 runs, 200/run)
      - Carbon Fiber x400 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x200  [raw]
        - Evaporite Deposits x200  [raw]
      - Oxy-Organic Solvents x2 [reaction] (1 run, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x2,000  [raw]
        - Atmospheric Gases x2,000  [raw]
      - Thermosetting Polymer x400 [reaction] (2 runs, 200/run)
        - Oxygen Fuel Block x10 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x200  [raw]
        - Silicates x200  [raw]
  - Auto-Integrity Preservation Seal x150 [manufacturing] (50 runs, 3/run)
    - Supertensile Plastics x200  [raw]
    - Nanites x200  [raw]
    - Reinforced Carbon Fiber x500 [reaction] (3 runs, 200/run)
      - Carbon Fiber x600 [reaction] (3 runs, 200/run)
        - Hydrogen Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x300  [raw]
        - Evaporite Deposits x300  [raw]
      - Oxy-Organic Solvents x3 [reaction] (1 run, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x2,000  [raw]
        - Atmospheric Gases x2,000  [raw]
      - Thermosetting Polymer x600 [reaction] (3 runs, 200/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 run, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x300  [raw]
        - Silicates x300  [raw]
  - Megacyte x1,950  [raw]
  - Zydrine x3,900  [raw]
  - Nocxium x15,600  [raw]
  - Isogen x130,000  [raw]
  - Mexallon x390,000  [raw]
  - Pyerite x2,600,000  [raw]
  - Tritanium x5,200,000  [raw]
```

## Aggregated phases (shared intermediates merged)

What M5's shared-quantity aggregation produces: same-type
requirements merge per phase, then round runs once — not per parent.
Phases count up in build order (decided 2026-11-18): raw-material
terminators sit at phase 0, the deepest buildable layer (fuel blocks)
is phase 1, the target is the highest number.

| Phase | Node | Qty | Activity | Runs |
|---|---|---|---|---|
| 5 | Typhoon | 1 | manufacturing | 1 |
| 4 | Core Temperature Regulator | 1 | manufacturing | 1 |
| 4 | Life Support Backup Unit | 75 | manufacturing | 25 |
| 4 | Auto-Integrity Preservation Seal | 150 | manufacturing | 50 |
| 3 | Pressurized Oxidizers | 500 | reaction | 3 |
| 3 | Reinforced Carbon Fiber | 1,250 | reaction | 7 |
| 2 | Carbon Polymers | 600 | reaction | 3 |
| 2 | Sulfuric Acid | 600 | reaction | 3 |
| 2 | Oxy-Organic Solvents | 10 | reaction | 1 |
| 2 | Carbon Fiber | 1,400 | reaction | 7 |
| 2 | Thermosetting Polymer | 1,400 | reaction | 7 |
| 1 | Helium Fuel Block | 15 | manufacturing | 1 |
| 1 | Nitrogen Fuel Block | 15 | manufacturing | 1 |
| 1 | Oxygen Fuel Block | 40 | manufacturing | 1 |
| 1 | Hydrogen Fuel Block | 35 | manufacturing | 1 |

**Aggregation savings** (per-branch → aggregated run counts):
Reinforced Carbon Fiber 3+2+3 = 8 → **7** runs; Carbon Fiber
600+400+600 → 1,400 = **7** runs (8 per-branch); Oxy-Organic
Solvents 3+2+3 = 8 needed → **10 = 1 run** (3 per-branch); Hydrogen
Fuel Block 40 → 35; Oxygen Fuel Block 50 → 40. This is the
per-phase-rounds-once payoff, and the same lever the M9
BPC (Blueprint Copy)/slot-splitting math pulls in the other direction.

## Raw-material acquisition table (Typhoon ×1)

All terminators summed across the whole chain — what to obtain, by
category and in-game mechanic. Reprocessing, PI (Planetary Industry), and ice products
are inputs to *acquire*, not plan: the chain planner stops here.

| Minerals | Qty | | Moon materials | Qty |
|---|---|---|---|---|
| Tritanium | 5,200,000 | | Hydrocarbons | 3,000 |
| Pyerite | 2,600,000 | | Atmospheric Gases | 3,000 |
| Mexallon | 390,000 | | Silicates | 1,000 |
| Isogen | 130,000 | | Evaporite Deposits | 1,000 |
| Nocxium | 15,600 | | | |
| Zydrine | 3,900 | | | |
| Megacyte | 1,950 | | | |

| PI commodities | Qty | | Ice products | Qty |
|---|---|---|---|---|
| Test Cultures | 200 | | Liquid Ozone | 1,400 |
| Viral Agent | 200 | | Heavy Water | 680 |
| Supertensile Plastics | 200 | | Helium Isotopes | 450 |
| Nanites | 200 | | Nitrogen Isotopes | 450 |
| Chiral Structures | 100 | | Oxygen Isotopes | 450 |
| Water | 100 | | Hydrogen Isotopes | 450 |
| Coolant | 36 | | Oxygen | 88 |
| Enriched Uranium | 16 | | Strontium Clathrates | 80 |
| Mechanical Parts | 16 | | | |
| Robotics | 4 | | | |

## Mechanics the expansion established

- **Reactions produce in batches**: most reaction formulas yield
  200/run (Oxy-Organic Solvents 10/run) — run counts stay small
  while quantities run large. Ceil-rounding shows up as overage
  (3 runs × 200 = 600 produced for 500 needed).
- **Component recipes yield 3/run** (Life Support Backup Unit,
  Auto-Integrity Preservation Seal): 75 units = 25 runs, 150 = 50.
  Per-run product quantity is real input to the run math.
- **Fuel blocks are the deepest manufacturing** (40/run) and feed
  the bottom reactions — activities interleave by dependency, not
  by phase type. The resolver cannot assume "manufacturing above,
  reactions below."
- **Four raw-material categories**: minerals, moon materials, PI
  commodities, ice products. The acquisition table groups by them
  because each maps to a different in-game acquisition mechanic.
- **Fuel-block inputs repeat verbatim** across isotopes — the four
  fuel-block recipes differ only in isotope type (and PI mix is
  constant: Robotics 1, Enriched Uranium 4, Mechanical Parts 4,
  Coolant 9, Strontium 20, Oxygen 22, Heavy Water 170, Liquid
  Ozone 350 per 40 blocks).

## Later: reprocessing efficiency (noted, not planned)

At some point the acquisition table wants a yield layer:
reprocessing compressed veldspar (etc.) into minerals, computed
from character skills, implants, and structure bonuses (reprocessing
rigs, faction-warfare system bonus, security status). Deliberately
out of the chain planner — parked in MILESTONES' Later tracks; this
table is the input it would calculate against.

## Work-distribution model — Typhoon ×100 (logic proof-out, 2026-11-16)

The M9-side reference: how 100 Typhoons distribute across the blitz
and blitz holdings slot pool. Computed from the live mirror and the
live roster (corp 98830898: Octavia Arbitrage, schlepzrage,
theblitzrage I; no active jobs at modeling time). **Model rules**,
stated so they can be challenged:

- Each commodity's runs spread across the full eligible slot pool —
  one BPC per slot, run count = even split with the remainder
  distributed round-robin across characters. `n×r` notation = the
  BPC mix a character holds.
- Commodities within a phase share the slots sequentially (waves);
  slot count per commodity is `min(runs, pool)`.
- Quantities are recomputed from scratch at ×100 — not scaled from
  the ×1 table — so ceil-rounding overage shrinks (Oxy-Organic
  Solvents 875 vs a naive 1,000; Oxygen Fuel Block 3,565 vs 4,000).
  M5's round-once-at-target-quantity principle, visible in numbers.
- **Assumptions**: max skills (10 slots per character per activity),
  ideal BPCs at whatever run count the split wants, all raw
  materials on hand, no efficiency weighting. One open flag:
  reactions are modeled with their own 10-slot pool — the actual
  skill→slot mapping is M9's confirm-from-dogma task, and if
  reactions share manufacturing slots, phases 2/3 merge into the
  same 30-slot pool and the wave counts combine.

```text
========================================================================
TYPHOON x100 — WORK DISTRIBUTION MODEL (logic proof-out)
========================================================================
Pool: blitz and blitz holdings (98830898)
  Octavia Arbitrage    10 manufacturing slots / 10 reaction slots
  schlepzrage          10 manufacturing slots / 10 reaction slots
  theblitzrage I       10 manufacturing slots / 10 reaction slots
Active jobs: none. Assumptions: max skills, ideal BPCs at preferred
run counts, all raw materials on hand, no efficiency weighting.

------------------------------------------------------------------------
PHASE 1 — MANUFACTURING  total 233 runs (120 jobs = 4 full waves + remainder)
------------------------------------------------------------------------
  Nitrogen Fuel Block      1,250 units ->  32 runs  [2 BPC x2 runs, 28 BPC x1 runs]
      Octavia Arbitrage   10 jobs     11 runs  (1x2, 9x1)
      schlepzrage         10 jobs     11 runs  (1x2, 9x1)
      theblitzrage I      10 jobs     10 runs  (10x1)
  Hydrogen Fuel Block      3,125 units ->  79 runs  [19 BPC x3 runs, 11 BPC x2 runs]
      Octavia Arbitrage   10 jobs     27 runs  (7x3, 3x2)
      schlepzrage         10 jobs     26 runs  (6x3, 4x2)
      theblitzrage I      10 jobs     26 runs  (6x3, 4x2)
  Helium Fuel Block        1,250 units ->  32 runs  [2 BPC x2 runs, 28 BPC x1 runs]
      Octavia Arbitrage   10 jobs     11 runs  (1x2, 9x1)
      schlepzrage         10 jobs     11 runs  (1x2, 9x1)
      theblitzrage I      10 jobs     10 runs  (10x1)
  Oxygen Fuel Block        3,565 units ->  90 runs  [30 BPC x3 runs]
      Octavia Arbitrage   10 jobs     30 runs  (10x3)
      schlepzrage         10 jobs     30 runs  (10x3)
      theblitzrage I      10 jobs     30 runs  (10x3)

------------------------------------------------------------------------
PHASE 2 — REACTION       total 1,838 runs (150 jobs = 5 full waves + remainder)
------------------------------------------------------------------------
  Carbon Polymers        50,000 units -> 250 runs  [10 BPC x9 runs, 20 BPC x8 runs]
      Octavia Arbitrage   10 jobs     84 runs  (4x9, 6x8)
      schlepzrage         10 jobs     83 runs  (3x9, 7x8)
      theblitzrage I      10 jobs     83 runs  (3x9, 7x8)
  Sulfuric Acid          50,000 units -> 250 runs  [10 BPC x9 runs, 20 BPC x8 runs]
      Octavia Arbitrage   10 jobs     84 runs  (4x9, 6x8)
      schlepzrage         10 jobs     83 runs  (3x9, 7x8)
      theblitzrage I      10 jobs     83 runs  (3x9, 7x8)
  Carbon Fiber          125,000 units -> 625 runs  [25 BPC x21 runs, 5 BPC x20 runs]
      Octavia Arbitrage   10 jobs    209 runs  (9x21, 1x20)
      schlepzrage         10 jobs    208 runs  (8x21, 2x20)
      theblitzrage I      10 jobs    208 runs  (8x21, 2x20)
  Oxy-Organic Solvents      875 units ->  88 runs  [28 BPC x3 runs, 2 BPC x2 runs]
      Octavia Arbitrage   10 jobs     30 runs  (10x3)
      schlepzrage         10 jobs     29 runs  (9x3, 1x2)
      theblitzrage I      10 jobs     29 runs  (9x3, 1x2)
  Thermosetting Polymer 125,000 units -> 625 runs  [25 BPC x21 runs, 5 BPC x20 runs]
      Octavia Arbitrage   10 jobs    209 runs  (9x21, 1x20)
      schlepzrage         10 jobs    208 runs  (8x21, 2x20)
      theblitzrage I      10 jobs    208 runs  (8x21, 2x20)

------------------------------------------------------------------------
PHASE 3 — REACTION       total   875 runs (60 jobs = 2 full waves + remainder)
------------------------------------------------------------------------
  Pressurized Oxidizers  50,000 units -> 250 runs  [10 BPC x9 runs, 20 BPC x8 runs]
      Octavia Arbitrage   10 jobs     84 runs  (4x9, 6x8)
      schlepzrage         10 jobs     83 runs  (3x9, 7x8)
      theblitzrage I      10 jobs     83 runs  (3x9, 7x8)
  Reinforced Carbon Fib 125,000 units -> 625 runs  [25 BPC x21 runs, 5 BPC x20 runs]
      Octavia Arbitrage   10 jobs    209 runs  (9x21, 1x20)
      schlepzrage         10 jobs    208 runs  (8x21, 2x20)
      theblitzrage I      10 jobs    208 runs  (8x21, 2x20)

------------------------------------------------------------------------
PHASE 4 — MANUFACTURING  total 7,600 runs (90 jobs = 3 full waves + remainder)
------------------------------------------------------------------------
  Auto-Integrity Preserv 15,000 units -> 5,000 runs  [20 BPC x167 runs, 10 BPC x166 runs]
      Octavia Arbitrage   10 jobs  1,667 runs  (7x167, 3x166)
      schlepzrage         10 jobs  1,667 runs  (7x167, 3x166)
      theblitzrage I      10 jobs  1,666 runs  (6x167, 4x166)
  Core Temperature Regu    100 units ->   100 runs  [10 BPC x4 runs, 20 BPC x3 runs]
      Octavia Arbitrage   10 jobs     34 runs  (4x4, 6x3)
      schlepzrage         10 jobs     33 runs  (3x4, 7x3)
      theblitzrage I      10 jobs     33 runs  (3x4, 7x3)
  Life Support Backup U  7,500 units -> 2,500 runs  [10 BPC x84 runs, 20 BPC x83 runs]
      Octavia Arbitrage   10 jobs    834 runs  (4x84, 6x83)
      schlepzrage         10 jobs    833 runs  (3x84, 7x83)
      theblitzrage I      10 jobs    833 runs  (3x84, 7x83)

------------------------------------------------------------------------
PHASE 5 — MANUFACTURING  total   100 runs (30 jobs = 1 full wave)
------------------------------------------------------------------------
  Typhoon                  100 units ->   100 runs  [10 BPC x4 runs, 20 BPC x3 runs]
      Octavia Arbitrage   10 jobs     34 runs  (4x4, 6x3)
      schlepzrage         10 jobs     33 runs  (3x4, 7x3)
      theblitzrage I      10 jobs     33 runs  (3x4, 7x3)

========================================================================
PER-CHARACTER TOTALS (slots reused across phases — sequential waves)
========================================================================
  Octavia Arbitrage   manufacturing:  80 jobs /  2,648 runs   reaction:  70 jobs /  909 runs
  schlepzrage         manufacturing:  80 jobs /  2,644 runs   reaction:  70 jobs /  902 runs
  theblitzrage I      manufacturing:  80 jobs /  2,641 runs   reaction:  70 jobs /  902 runs
```

What the model demonstrates for M9's design: the even-split
round-robin produces near-identical per-character loads (within a
run or two); the BPC mixes per commodity are the "preferred run
count" outputs the copy-planning recommendation would produce; wave
counts (4/5/2/3/1) are how a phase's jobs serialize on the shared
slot pool; and the throughput end of the slider is exactly this —
all slots filled, run counts whatever the split yields, no
efficiency weighting.

## Time-balanced model v2 (2026-11-17)

Re-balances v1 for **time**: jobs sized so each phase's jobs end
approximately together (deliverable at one login), 6-hour login
windows, and the real BPO constraints. Assumptions: max skills
(manufacturing ×0.68 — Industry 5 × Advanced Industry 5, **flagged
for dogma verification**; reaction and copy times unadjusted);
reactions cannot be copied — each character holds 1 BPO per formula,
so a formula runs at most 3 concurrent jobs (one per character), all
within their 10 reaction slots; copying is 1 job per BPO (science
slots, ~8 concurrent streams across the roster); BPC run counts
respect `maxProductionLimit` (Typhoon 10, CTR — Core Temperature
Regulator — 40, components/fuel blocks 200).

| Phase | Activity | Duration | Job shape |
|---|---|---|---|
| 1 — fuel blocks | mfg | ~1h (1 window) | 16–30 BPCs of 2–3 runs each |
| 2 — reactions | rxn | 627h = 105 windows = 26.2d | 3 BPO jobs per formula (209/208/208 on the 625-run formulas) |
| 3 — reactions | rxn | 627h = 26.2d | same BPO-bound shape |
| 4 — components | mfg | ~90 slot-hours, 3 waves | AIPS — Auto-Integrity Preservation Seal — 30 BPCs ×~167, LSBU — Life Support Backup Unit — 30 ×~84, CTR 25 ×4 |
| 5 — Typhoons | mfg | ~17h | 25 BPCs ×4 runs |

**Copy pipeline** (parallel from chain start, sequential per BPO):

| commodity | BPCs | run counts | copy hours | ready |
|---|---|---|---|---|
| Auto-Integrity Preservation Seal | 30 | 20×167, 10×166 | 2,000 | 83.3d |
| Life Support Backup Unit | 30 | 10×84, 20×83 | 1,000 | 41.7d |
| Typhoon | 25 | 25×4 | 400 | 16.7d |
| Core Temperature Regulator | 25 | 25×4 | 178 | 7.4d |
| Oxygen/Hydrogen/Helium/Nitrogen fuel blocks | 30/27/16/16 | 2–3 each | 6–18 | <1d |

**Findings**: chain ≈ 88 days pure-copy; the single AIPS BPO's copy
queue (5,000 runs × 24 min = 2,000h) is the critical path; the
reaction phases (52.4d combined) finish 30 days early and wait;
manufacturing slots run ~5% utilized — never the constraint. The
end-together sizing needs only ~7 logins across the whole chain.
Pipelining (partial reaction deliveries, BPCs building as they
arrive) is deliberately excluded to keep phases deliver-together.

## Copy-vs-direct decision rule

Per commodity with R runs, copy time t_c/run, skilled build time
t_b/run, inputs arriving at T_in (the dead zone):

1. **Queue fits the dead zone (R·t_c ≤ T_in): copy everything** —
   copying converts BPO time that couldn't build anyway into
   parallel capacity. No diminishing return inside the dead zone.
2. **Queue overflows (R·t_c > T_in) and t_b < t_c: switch to direct
   at exactly T_in** — copy full-bore until inputs exist, then build
   direct for the remainder (each post-T_in copy-hour yields 1/t_c
   runs where a build-hour yields 1/t_b).
3. **t_b ≥ t_c (low skills): never switch** — copying is per-hour
   better. Break-even multiplier = t_c/t_base (0.80 for AIPS:
   Industry 5 alone lands exactly on it).

AIPS at ×100: pure copy finishes day ~86; **hybrid (copy to day 53,
then direct) day ~79**; pure direct day ~124 — the trap is that
direct building can't start before RCF (Reinforced Carbon Fiber) inputs exist, so the BPO
idles. Copying's real value is monetizing BPO dead time, not slot
parallelism. Useful BPO count = ceil(R·t_c / T_in) — beyond that,
BPOs idle.

## Target-count scaling & timelines

All quantities are linear in N, so ratios never move: AIPS copy
queue ÷ reaction dead zone = 1.6 at every N; slot utilization ~5% at
every N. There is **no slot-based ideal target count** — 100 is not
too large for 30 slots (they idle regardless); it is too large for
one AIPS BPO and for an 88-day deadline. The AIPS overflow is
proportional at every N (≈0.3 days of dead wait per Typhoon —
sub-day below N ≈ 3, the dominant chain term by N ≈ 30); there is
no fits/doesn't-fit threshold, and target count is purely a deadline
choice:

| horizon | pure copy | hybrid | 2 AIPS BPOs |
|---|---|---|---|
| 7d | 7 | 8 | 12 |
| 14d | 15 | 17 | 24 |
| 30d | 34 | 37 | 52 |
| 60d | 68 | 75 | 104 |
| 90d | 102 | 113 | 157 |

Timelines (pure-copy strategy; `#` copy, `r` reaction — rows "rxn", `m`
manufacturing — rows "mfg", `.` dead zone):

```text
TYPHOON x10 — chain end 9.5d, dead wait 3.0d
  AIPS copy     |##################################################  | 0.0 ->  8.3d
  LSBU copy     |#########################                           | 0.0 ->  4.2d
  TYPHOON copy  |##########                                        | 0.0 ->  1.7d
  phase 2 rxn   |rrrrrrrrrrrrrrrr                                   | 0.1 ->  2.7d
  phase 3 rxn   |                rrrrrrrrrrrrrrrr                   | 2.7 ->  5.3d
  BUILDS WAIT   |                                ..................  | 5.3 ->  8.3d
  phase 4 mfg   |                                                  m| 8.3 ->  8.9d
  phase 5 mfg   |                                                   | 8.9 ->  9.5d

TYPHOON x25 — chain end 22.5d, dead wait 7.6d
  AIPS copy     |#####################################################| 0.0 -> 20.8d
  LSBU copy     |##########################                          | 0.0 -> 10.4d
  TYPHOON copy  |##########                                         | 0.0 ->  4.2d
  phase 2 rxn   |rrrrrrrrrrrrrrrrr                                  | 0.2 ->  6.7d
  phase 3 rxn   |                 rrrrrrrrrrrrrrrrr                 | 6.7 -> 13.3d
  BUILDS WAIT   |                                  ...................|13.3 -> 20.8d
  phase 4 mfg   |                                                    |20.8 -> 22.0d
  phase 5 mfg   |                                                    |22.0 -> 22.5d

TYPHOON x50 — chain end 44.3d, dead wait 15.2d
  AIPS copy     |######################################################| 0.0 -> 41.7d
  LSBU copy     |###########################                         | 0.0 -> 20.8d
  TYPHOON copy  |###########                                        | 0.0 ->  8.3d
  phase 2 rxn   |rrrrrrrrrrrrrrrrr                                  | 0.4 -> 13.4d
  phase 3 rxn   |                 rrrrrrrrrrrrrrrrr                 |13.4 -> 26.5d
  BUILDS WAIT   |                                  ....................|26.5 -> 41.7d
  phase 4 mfg   |                                                     |41.7 -> 43.7d
  phase 5 mfg   |                                                     |43.7 -> 44.3d

TYPHOON x100 — chain end 87.9d, dead wait 30.4d
  AIPS copy     |#######################################################| 0.0 -> 83.3d
  LSBU copy     |###########################                          | 0.0 -> 41.7d
  TYPHOON copy  |###########                                          | 0.0 -> 16.7d
  phase 2 rxn   |rrrrrrrrrrrrrrrrr                                    | 0.8 -> 26.8d
  phase 3 rxn   |                 rrrrrrrrrrrrrrrrr                   |26.8 -> 52.9d
  BUILDS WAIT   |                                  .....................|52.9 -> 83.3d
  phase 4 mfg   |                                                       |83.3 -> 87.3d
  phase 5 mfg   |                                                       |87.3 -> 87.9d
```

| N | end | d/Typhoon | reactions done | AIPS copy | dead wait | copy÷T_in |
|---|---|---|---|---|---|---|
| 3 | 3.4d | 1.13 | 1.6d | 2.5d | 0.9d | 1.53 |
| 10 | 9.5d | 0.95 | 5.3d | 8.3d | 3.0d | 1.56 |
| 25 | 22.5d | 0.90 | 13.3d | 20.8d | 7.6d | 1.57 |
| 50 | 44.3d | 0.89 | 26.5d | 41.7d | 15.2d | 1.57 |
| 100 | 87.9d | 0.88 | 52.9d | 83.3d | 30.4d | 1.58 |
| 200 | 175.5d | 0.88 | 105.7d | 166.7d | 60.9d | 1.58 |

## BPO obtainment recommendations

The inverse question — given a target (or deadline), which BPOs to
acquire. Rules are closed-form and **scale-invariant**: minimum
useful BPOs per commodity = ceil(queue rate ÷ dead-zone rate), which
does not grow with N.

- **Trigger**: the AIPS queue overflows the dead zone at every N
  (sub-day below N ≈ 3); a ~1-day dead-wait tolerance puts the
  practical trigger near **N ≈ 4 Typhoons** — from there up,
  "acquire a second AIPS BPO" is the standing recommendation.
- **Ceiling**: BPOs eventually saturate slots (~35 for AIPS at 30
  slots); between the minimum and the ceiling, extras idle.
- **Ladder** (un-gating one resource exposes the next):

| rung | assets | chain rate | gated by |
|---|---|---|---|
| today | 1 AIPS BPO, 1 rxn BPO/char/formula | 0.88 d/N | AIPS copying |
| +1 AIPS BPO | 2 AIPS | 0.58 d/N | reactions — best single purchase |
| +1 rxn BPO/char/formula, AIPS→4, LSBU→2 | | 0.32 d/N | reaction slots (phase 2: 5 formulas × 2 jobs/char = 10 slots exactly) |
| beyond | stagger formulas, more of everything | →0.04–0.1 d/N | manufacturing slots / wave quantization |

## Deterministic feasibility

Every computation in this document is closed-form arithmetic over
the SDE mirror plus the synced `skills`/`blueprints` tables — chain
resolution is a graph walk, rates are linear in N, scheduling is
even-split + ceil quantization, and the recommendation rules are
divisions. No LLM is involved at runtime; these numbers are golden
test values for the calculators. **The executable versions live in
`reference/`** (`chain_expand.py`, `timeline_model.py`, plus a
formula reference in `reference/README.md`) — they regenerate this
document's values and are the spec M4/M5/M9/M12 graduate into the
app. Skill multipliers are computed per character from the synced
`skills` table there, never taken as a global constant (the 0.68
here is the max-skills scenario). The unpinned inputs are the
skill→time/copy multipliers (dogma verification) and the reaction
slot/BPO-lock semantics — data problems, not algorithm problems.
