# The Typhoon chain — full reference

The completely expanded production chain for the **Typhoon** (T1
battleship, type 644, blueprint 998) at target quantity ×1 — the
worked example M5's chain resolution gets checked against. This file
exists because the full expansion is too heavy for `MILESTONES.md`
or `TODO.md`, but the detail matters: batch sizes, per-run product
quantities, shared intermediates, and the raw-material totals all
shape the resolver's design.

Provenance: read directly from the live SDE mirror (`sde_*` tables,
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

```
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
Target = phase 0, terminators below phase 4.

| Phase | Node | Qty | Activity | Runs |
|---|---|---|---|---|
| 0 | Typhoon | 1 | manufacturing | 1 |
| 1 | Core Temperature Regulator | 1 | manufacturing | 1 |
| 1 | Life Support Backup Unit | 75 | manufacturing | 25 |
| 1 | Auto-Integrity Preservation Seal | 150 | manufacturing | 50 |
| 2 | Pressurized Oxidizers | 500 | reaction | 3 |
| 2 | Reinforced Carbon Fiber | 1,250 | reaction | 7 |
| 3 | Carbon Polymers | 600 | reaction | 3 |
| 3 | Sulfuric Acid | 600 | reaction | 3 |
| 3 | Oxy-Organic Solvents | 10 | reaction | 1 |
| 3 | Carbon Fiber | 1,400 | reaction | 7 |
| 3 | Thermosetting Polymer | 1,400 | reaction | 7 |
| 4 | Helium Fuel Block | 15 | manufacturing | 1 |
| 4 | Nitrogen Fuel Block | 15 | manufacturing | 1 |
| 4 | Oxygen Fuel Block | 40 | manufacturing | 1 |
| 4 | Hydrogen Fuel Block | 35 | manufacturing | 1 |

**Aggregation savings** (per-branch → aggregated run counts):
Reinforced Carbon Fiber 3+2+3 = 8 → **7** runs; Carbon Fiber
600+400+600 → 1,400 = **7** runs (8 per-branch); Oxy-Organic
Solvents 3+2+3 = 8 needed → **10 = 1 run** (3 per-branch); Hydrogen
Fuel Block 40 → 35; Oxygen Fuel Block 50 → 40. This is the
per-phase-rounds-once payoff, and the same lever the M9
BPC/slot-splitting math pulls in the other direction.

## Raw-material acquisition table (Typhoon ×1)

All terminators summed across the whole chain — what to obtain, by
category and in-game mechanic. Reprocessing, PI, and ice products
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
