# The Hel chain — full reference

Eighth chain document (after `TYPHOON-CHAIN.md` through
`CRASH-CHAIN.md`), added 2026-11-21 for the **supercapital tier,
gentler half** of the roadmap's climax pair: the Hel Minmatar
supercarrier ×1. The set piece is **convergence** — one chain that
nests three previous chains' worlds at once: the Charon's capital
components at roughly ten times its bill (Auto-Integrity
Preservation Seal ×800, Life Support Backup Unit ×400, fourteen
capital component types), the Jackdaw's fullerene-polymer world at
roughly a hundred times its bill (nine fullerites totalling
~757,000 units), and a brand-new **neurolink component family**
(G-O Trigger Neurolink Conduit, Ladar-FTL Interlink Communicator,
Enhanced Neurolink Protection Cell) that reaches through
molecular-forged reactions into the full k-space gas family. Every
deterministic number here is output of the reference scripts —
regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 22852 1
```

Provenance: read from the live SDE (Static Data Export) mirror
(release 2026-11-20) and the synced live tables (ownership, skills,
stock — 2026-11-21). Phases count up in build order (terminators =
phase 0, target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Hel ×1)

- IDs: Hel **22852**, Blueprint **22853** (maxProductionLimit **1**,
  6,000,000 s build — **69.4 d unskilled, 47.2 d at the max-skills
  0.68 multiplier**: the longest build in the program by an order of
  magnitude; the Jackdaw's 50 h hull was the previous record).
  Copy activity exists (4.8M s) but is moot — see acquisition.
- **The Hel Blueprint has no BPC source in the SDE** — not invented,
  not NPC-seeded, no producer: supercapital BPCs come from rare
  in-game drops and are acquired by contract (the drop-sourced path
  at hull scale; **pin the drop source, verify against M15 contract
  data**). maxPL 1 means the BPC builds exactly one Hel.
- **18 hull materials**: the Charon's capital set at ~10× (AIPS ×800,
  LSBU ×400, Capital Drone Bay ×250, plus eleven more capital
  component types), the supercapital-specific **Ladar-FTL Interlink
  Communicator ×125** (fullerene polymers, Plasmonic Metamaterials,
  and Fermionic Condensates — the Jackdaw and Panther reaction
  worlds in one component), the **G-O Trigger Neurolink Conduit ×64**
  and **Enhanced Neurolink Protection Cell ×1** (the new neurolink
  family), and Capital Jump Drive ×100 (the Panther's crossover
  component, back at super scale).
- **Scale by the numbers**: 7 buildable phases (matching the
  Charon's depth at several times its breadth) · **79 buildable
  commodity types** · 4,201 manufacturing runs · **10,478 reaction
  runs** (31,434 reaction slot-hours — 1,310 d single-slot) ·
  1,029 fuel-block runs · **79 raw types** across six categories —
  every one a program record.
- **The mineral mountain**: Pyerite **146.8M**, Tritanium 43.7M,
  Mexallon 41.1M, Isogen 11.5M — an order of magnitude past the
  Charon's bill; the largest material procurement in the program.
- **Recurring commodities at their extreme**: all four fuel-block
  types recur at **three phase levels each**, and six reaction
  products (Reinforced Carbon Fiber, Carbon Fiber, Pressurized
  Oxidizers, Carbon Polymers, Sulfuric Acid, Thermosetting Polymer,
  Oxy-Organic Solvents) at two levels each — the merged-campaign
  question (M5/M9) is this chain's defining scheduling feature, not
  an edge case.
- Skills: **Capital Ship Construction 4** gates the hull (held at
  level **1** by Octavia Arbitrage, the sole holder — a 3-level live
  gap, the skill-plan calculator TODO item's natural customer);
  reaction tiers per the component families (Reactions 2-3, held);
  the neurolink molecular-forged formulas gate on Reactions 3.
- **Blueprint inventory: 79 types — 44 owned, 35 missing**. The
  owned set is the Charon/Typhoon world carrying over wholesale
  (AIPS, LSBU, CTR, all four fuel-block BPs, the polymer and simple
  reaction formulas, and — new — the Isotropic Neofullerene and
  neurolink-stabilizer formulas the roster already holds). Missing:
  all fourteen capital/supercapital component BPs, the Hel BP
  itself (contract), and twelve reaction formulas (the advanced
  composite stack: Fermionic Condensates, Plasmonic Metamaterials,
  Dysporite, Prometium, Fluxed Condensates, plus neurolink and
  Fernite Alloy formulas).
- **From zero on everything super-relevant**: no Hel BP, no capital
  component BPs, no capital component stock, and the mineral
  mountain dwarfs current holdings (Tritanium 97.4M on hand against
  43.7M needed — the one covered mineral; Pyerite stock is
  hundreds of thousands against 146.8M needed).
- **Structure-only build** (community-documented): supercapitals
  build exclusively in structures with the supercapital assembly
  capability — the M3 structure manager must model a distinct
  facility class; **pin at M3**.

## Per-branch tree (Hel ×1)

```text
- Hel x1 [manufacturing] (1 runs, 1/run)
  - Capital Propulsion Engine x50 [manufacturing] (50 runs, 1/run)
    - Self-Harmonizing Power Core x50  [raw]
    - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
      - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,500  [raw]
        - Evaporite Deposits x2,500  [raw]
      - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x6,000  [raw]
        - Atmospheric Gases x6,000  [raw]
      - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
        - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
        - Silicates x2,500  [raw]
    - Megacyte x14,250  [raw]
    - Zydrine x28,500  [raw]
    - Nocxium x56,250  [raw]
    - Isogen x562,500  [raw]
    - Tritanium x2,025,000  [raw]
    - Mexallon x2,025,000  [raw]
    - Pyerite x7,312,500  [raw]
  - Capital Sensor Cluster x40 [manufacturing] (40 runs, 1/run)
    - Broadcast Node x40  [raw]
    - Reinforced Carbon Fiber x4,000 [reaction] (20 runs, 200/run)
      - Carbon Fiber x4,000 [reaction] (20 runs, 200/run)
        - Hydrogen Fuel Block x100 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Hydrogen Isotopes x1,350  [raw]
        - Hydrocarbons x2,000  [raw]
        - Evaporite Deposits x2,000  [raw]
      - Oxy-Organic Solvents x20 [reaction] (2 runs, 10/run)
        - Oxygen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x4,000  [raw]
        - Atmospheric Gases x4,000  [raw]
      - Thermosetting Polymer x4,000 [reaction] (20 runs, 200/run)
        - Oxygen Fuel Block x100 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Oxygen Isotopes x1,350  [raw]
        - Atmospheric Gases x2,000  [raw]
        - Silicates x2,000  [raw]
    - Megacyte x11,400  [raw]
    - Zydrine x22,800  [raw]
    - Nocxium x45,000  [raw]
    - Isogen x450,000  [raw]
    - Tritanium x1,620,000  [raw]
    - Mexallon x1,620,000  [raw]
    - Pyerite x5,850,000  [raw]
  - Capital Armor Plates x50 [manufacturing] (50 runs, 1/run)
    - Organic Mortar Applicators x250  [raw]
    - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
      - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,500  [raw]
        - Evaporite Deposits x2,500  [raw]
      - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x6,000  [raw]
        - Atmospheric Gases x6,000  [raw]
      - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
        - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
        - Silicates x2,500  [raw]
    - Megacyte x15,400  [raw]
    - Zydrine x30,750  [raw]
    - Nocxium x60,000  [raw]
    - Isogen x600,000  [raw]
    - Tritanium x2,250,000  [raw]
    - Mexallon x2,250,000  [raw]
    - Pyerite x7,875,000  [raw]
  - Capital Capacitor Battery x150 [manufacturing] (150 runs, 1/run)
    - Self-Harmonizing Power Core x150  [raw]
    - Reinforced Carbon Fiber x15,000 [reaction] (75 runs, 200/run)
      - Carbon Fiber x15,000 [reaction] (75 runs, 200/run)
        - Hydrogen Fuel Block x375 [manufacturing] (10 runs, 40/run)
          - Robotics x10  [raw]
          - Enriched Uranium x40  [raw]
          - Mechanical Parts x40  [raw]
          - Coolant x90  [raw]
          - Strontium Clathrates x200  [raw]
          - Oxygen x220  [raw]
          - Heavy Water x1,700  [raw]
          - Liquid Ozone x3,500  [raw]
          - Hydrogen Isotopes x4,500  [raw]
        - Hydrocarbons x7,500  [raw]
        - Evaporite Deposits x7,500  [raw]
      - Oxy-Organic Solvents x75 [reaction] (8 runs, 10/run)
        - Oxygen Fuel Block x40 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x16,000  [raw]
        - Atmospheric Gases x16,000  [raw]
      - Thermosetting Polymer x15,000 [reaction] (75 runs, 200/run)
        - Oxygen Fuel Block x375 [manufacturing] (10 runs, 40/run)
          - Robotics x10  [raw]
          - Enriched Uranium x40  [raw]
          - Mechanical Parts x40  [raw]
          - Coolant x90  [raw]
          - Strontium Clathrates x200  [raw]
          - Oxygen x220  [raw]
          - Heavy Water x1,700  [raw]
          - Liquid Ozone x3,500  [raw]
          - Oxygen Isotopes x4,500  [raw]
        - Atmospheric Gases x7,500  [raw]
        - Silicates x7,500  [raw]
    - Megacyte x41,700  [raw]
    - Zydrine x82,200  [raw]
    - Nocxium x168,750  [raw]
    - Isogen x1,687,500  [raw]
    - Tritanium x5,850,000  [raw]
    - Mexallon x5,850,000  [raw]
    - Pyerite x21,375,000  [raw]
  - Capital Power Generator x50 [manufacturing] (50 runs, 1/run)
    - Self-Harmonizing Power Core x50  [raw]
    - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
      - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,500  [raw]
        - Evaporite Deposits x2,500  [raw]
      - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x6,000  [raw]
        - Atmospheric Gases x6,000  [raw]
      - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
        - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
        - Silicates x2,500  [raw]
    - Megacyte x16,500  [raw]
    - Zydrine x33,000  [raw]
    - Nocxium x67,500  [raw]
    - Isogen x675,000  [raw]
    - Tritanium x2,362,500  [raw]
    - Mexallon x2,362,500  [raw]
    - Pyerite x8,437,500  [raw]
  - Capital Shield Emitter x100 [manufacturing] (100 runs, 1/run)
    - Recursive Computing Module x100  [raw]
    - Reinforced Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
      - Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
        - Hydrogen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Hydrogen Isotopes x3,150  [raw]
        - Hydrocarbons x5,000  [raw]
        - Evaporite Deposits x5,000  [raw]
      - Oxy-Organic Solvents x50 [reaction] (5 runs, 10/run)
        - Oxygen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x10,000  [raw]
        - Atmospheric Gases x10,000  [raw]
      - Thermosetting Polymer x10,000 [reaction] (50 runs, 200/run)
        - Oxygen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Oxygen Isotopes x3,150  [raw]
        - Atmospheric Gases x5,000  [raw]
        - Silicates x5,000  [raw]
    - Megacyte x30,800  [raw]
    - Zydrine x61,500  [raw]
    - Nocxium x120,000  [raw]
    - Isogen x1,200,000  [raw]
    - Tritanium x4,500,000  [raw]
    - Mexallon x4,500,000  [raw]
    - Pyerite x15,750,000  [raw]
  - Capital Jump Drive x100 [manufacturing] (100 runs, 1/run)
    - Wetware Mainframe x100  [raw]
    - Reinforced Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
      - Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
        - Hydrogen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Hydrogen Isotopes x3,150  [raw]
        - Hydrocarbons x5,000  [raw]
        - Evaporite Deposits x5,000  [raw]
      - Oxy-Organic Solvents x50 [reaction] (5 runs, 10/run)
        - Oxygen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x10,000  [raw]
        - Atmospheric Gases x10,000  [raw]
      - Thermosetting Polymer x10,000 [reaction] (50 runs, 200/run)
        - Oxygen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Oxygen Isotopes x3,150  [raw]
        - Atmospheric Gases x5,000  [raw]
        - Silicates x5,000  [raw]
    - Megacyte x42,000  [raw]
    - Zydrine x90,000  [raw]
    - Nocxium x168,800  [raw]
    - Isogen x1,687,500  [raw]
    - Tritanium x6,000,000  [raw]
    - Mexallon x6,000,000  [raw]
    - Pyerite x21,600,000  [raw]
  - Capital Drone Bay x250 [manufacturing] (250 runs, 1/run)
    - Broadcast Node x250  [raw]
    - Reinforced Carbon Fiber x25,000 [reaction] (125 runs, 200/run)
      - Carbon Fiber x25,000 [reaction] (125 runs, 200/run)
        - Hydrogen Fuel Block x625 [manufacturing] (16 runs, 40/run)
          - Robotics x16  [raw]
          - Enriched Uranium x64  [raw]
          - Mechanical Parts x64  [raw]
          - Coolant x144  [raw]
          - Strontium Clathrates x320  [raw]
          - Oxygen x352  [raw]
          - Heavy Water x2,720  [raw]
          - Liquid Ozone x5,600  [raw]
          - Hydrogen Isotopes x7,200  [raw]
        - Hydrocarbons x12,500  [raw]
        - Evaporite Deposits x12,500  [raw]
      - Oxy-Organic Solvents x125 [reaction] (13 runs, 10/run)
        - Oxygen Fuel Block x65 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x26,000  [raw]
        - Atmospheric Gases x26,000  [raw]
      - Thermosetting Polymer x25,000 [reaction] (125 runs, 200/run)
        - Oxygen Fuel Block x625 [manufacturing] (16 runs, 40/run)
          - Robotics x16  [raw]
          - Enriched Uranium x64  [raw]
          - Mechanical Parts x64  [raw]
          - Coolant x144  [raw]
          - Strontium Clathrates x320  [raw]
          - Oxygen x352  [raw]
          - Heavy Water x2,720  [raw]
          - Liquid Ozone x5,600  [raw]
          - Oxygen Isotopes x7,200  [raw]
        - Atmospheric Gases x12,500  [raw]
        - Silicates x12,500  [raw]
    - Megacyte x43,250  [raw]
    - Zydrine x84,500  [raw]
    - Nocxium x168,750  [raw]
    - Isogen x1,687,500  [raw]
    - Tritanium x6,093,750  [raw]
    - Mexallon x6,093,750  [raw]
    - Pyerite x22,500,000  [raw]
  - Capital Computer System x10 [manufacturing] (10 runs, 1/run)
    - Recursive Computing Module x10  [raw]
    - Reinforced Carbon Fiber x1,000 [reaction] (5 runs, 200/run)
      - Carbon Fiber x1,000 [reaction] (5 runs, 200/run)
        - Hydrogen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x500  [raw]
        - Evaporite Deposits x500  [raw]
      - Oxy-Organic Solvents x5 [reaction] (1 runs, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 runs, 40/run)
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
      - Thermosetting Polymer x1,000 [reaction] (5 runs, 200/run)
        - Oxygen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x500  [raw]
        - Silicates x500  [raw]
    - Megacyte x2,850  [raw]
    - Zydrine x5,700  [raw]
    - Nocxium x11,250  [raw]
    - Isogen x112,500  [raw]
    - Tritanium x405,000  [raw]
    - Mexallon x405,000  [raw]
    - Pyerite x1,462,500  [raw]
  - Capital Construction Parts x50 [manufacturing] (50 runs, 1/run)
    - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
      - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,500  [raw]
        - Evaporite Deposits x2,500  [raw]
      - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x6,000  [raw]
        - Atmospheric Gases x6,000  [raw]
      - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
        - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
        - Silicates x2,500  [raw]
    - Megacyte x10,500  [raw]
    - Zydrine x20,650  [raw]
    - Nocxium x37,500  [raw]
    - Isogen x450,000  [raw]
    - Tritanium x1,500,000  [raw]
    - Mexallon x1,500,000  [raw]
    - Pyerite x5,250,000  [raw]
  - Capital Ship Maintenance Bay x100 [manufacturing] (100 runs, 1/run)
    - Integrity Response Drones x100  [raw]
    - Reinforced Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
      - Carbon Fiber x10,000 [reaction] (50 runs, 200/run)
        - Hydrogen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Hydrogen Isotopes x3,150  [raw]
        - Hydrocarbons x5,000  [raw]
        - Evaporite Deposits x5,000  [raw]
      - Oxy-Organic Solvents x50 [reaction] (5 runs, 10/run)
        - Oxygen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x10,000  [raw]
        - Atmospheric Gases x10,000  [raw]
      - Thermosetting Polymer x10,000 [reaction] (50 runs, 200/run)
        - Oxygen Fuel Block x250 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Oxygen Isotopes x3,150  [raw]
        - Atmospheric Gases x5,000  [raw]
        - Silicates x5,000  [raw]
    - Megacyte x37,500  [raw]
    - Zydrine x75,000  [raw]
    - Nocxium x150,000  [raw]
    - Isogen x1,500,000  [raw]
    - Tritanium x5,400,000  [raw]
    - Mexallon x5,400,000  [raw]
    - Pyerite x19,200,000  [raw]
  - Capital Corporate Hangar Bay x50 [manufacturing] (50 runs, 1/run)
    - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
      - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,500  [raw]
        - Evaporite Deposits x2,500  [raw]
      - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
        - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x6,000  [raw]
        - Atmospheric Gases x6,000  [raw]
      - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
        - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
        - Silicates x2,500  [raw]
    - Megacyte x19,900  [raw]
    - Zydrine x39,400  [raw]
    - Nocxium x82,500  [raw]
    - Isogen x825,000  [raw]
    - Tritanium x2,812,500  [raw]
    - Mexallon x2,812,500  [raw]
    - Pyerite x10,125,000  [raw]
  - G-O Trigger Neurolink Conduit x64 [manufacturing] (64 runs, 1/run)
    - Pressurized Oxidizers x640 [reaction] (4 runs, 200/run)
      - Carbon Polymers x800 [reaction] (4 runs, 200/run)
        - Helium Fuel Block x20 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Hydrocarbons x400  [raw]
        - Silicates x400  [raw]
      - Sulfuric Acid x800 [reaction] (4 runs, 200/run)
        - Nitrogen Fuel Block x20 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Atmospheric Gases x400  [raw]
        - Evaporite Deposits x400  [raw]
      - Oxy-Organic Solvents x4 [reaction] (1 runs, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 runs, 40/run)
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
    - Reinforced Carbon Fiber x640 [reaction] (4 runs, 200/run)
      - Carbon Fiber x800 [reaction] (4 runs, 200/run)
        - Hydrogen Fuel Block x20 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x400  [raw]
        - Evaporite Deposits x400  [raw]
      - Oxy-Organic Solvents x4 [reaction] (1 runs, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 runs, 40/run)
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
      - Thermosetting Polymer x800 [reaction] (4 runs, 200/run)
        - Oxygen Fuel Block x20 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x400  [raw]
        - Silicates x400  [raw]
    - Sense-Heuristic Neurolink Enhancer x2,560 [reaction] (128 runs, 20/run)
      - Hydrogen Fuel Block x640 [manufacturing] (16 runs, 40/run)
        - Robotics x16  [raw]
        - Enriched Uranium x64  [raw]
        - Mechanical Parts x64  [raw]
        - Coolant x144  [raw]
        - Strontium Clathrates x320  [raw]
        - Oxygen x352  [raw]
        - Heavy Water x2,720  [raw]
        - Liquid Ozone x5,600  [raw]
        - Hydrogen Isotopes x7,200  [raw]
      - Azure Mykoserocin x5,120  [raw]
      - Vermillion Mykoserocin x5,120  [raw]
      - AV-Composite Molecular Condenser x128  [raw]
    - Goal-Orienting Neurolink Stabilizer x64 [reaction] (7 runs, 10/run)
      - Hydrogen Fuel Block x35 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Vermillion Cytoserocin x70  [raw]
      - Azure Cytoserocin x70  [raw]
      - AV-Composite Molecular Condenser x7  [raw]
  - Ladar-FTL Interlink Communicator x125 [manufacturing] (125 runs, 1/run)
    - Self-Harmonizing Power Core x125  [raw]
    - Wetware Mainframe x125  [raw]
    - Broadcast Node x250  [raw]
    - Fermionic Condensates x5,000 [reaction] (25 runs, 200/run)
      - Helium Fuel Block x125 [manufacturing] (4 runs, 40/run)
        - Robotics x4  [raw]
        - Enriched Uranium x16  [raw]
        - Mechanical Parts x16  [raw]
        - Coolant x36  [raw]
        - Strontium Clathrates x80  [raw]
        - Oxygen x88  [raw]
        - Heavy Water x680  [raw]
        - Liquid Ozone x1,400  [raw]
        - Helium Isotopes x1,800  [raw]
      - Caesarium Cadmide x2,500 [reaction] (13 runs, 200/run)
        - Oxygen Fuel Block x65 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Cadmium x1,300  [raw]
        - Caesium x1,300  [raw]
      - Dysporite x2,500 [reaction] (13 runs, 200/run)
        - Helium Fuel Block x65 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Helium Isotopes x900  [raw]
        - Mercury x1,300  [raw]
        - Dysprosium x1,300  [raw]
      - Fluxed Condensates x2,500 [reaction] (13 runs, 200/run)
        - Oxygen Fuel Block x65 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Neodymium x1,300  [raw]
        - Thulium x1,300  [raw]
      - Prometium x2,500 [reaction] (13 runs, 200/run)
        - Oxygen Fuel Block x65 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Cadmium x1,300  [raw]
        - Promethium x1,300  [raw]
    - Scandium Metallofullerene x16,250 [reaction] (102 runs, 160/run)
      - Helium Fuel Block x510 [manufacturing] (13 runs, 40/run)
        - Robotics x13  [raw]
        - Enriched Uranium x52  [raw]
        - Mechanical Parts x52  [raw]
        - Coolant x117  [raw]
        - Strontium Clathrates x260  [raw]
        - Oxygen x286  [raw]
        - Heavy Water x2,210  [raw]
        - Liquid Ozone x4,550  [raw]
        - Helium Isotopes x5,850  [raw]
      - Zydrine x2,550  [raw]
      - Fullerite-C72 x10,200  [raw]
      - Fullerite-C28 x10,200  [raw]
    - PPD Fullerene Fibers x23,750 [reaction] (95 runs, 250/run)
      - Hydrogen Fuel Block x475 [manufacturing] (12 runs, 40/run)
        - Robotics x12  [raw]
        - Enriched Uranium x48  [raw]
        - Mechanical Parts x48  [raw]
        - Coolant x108  [raw]
        - Strontium Clathrates x240  [raw]
        - Oxygen x264  [raw]
        - Heavy Water x2,040  [raw]
        - Liquid Ozone x4,200  [raw]
        - Hydrogen Isotopes x5,400  [raw]
      - Fullerite-C60 x9,500  [raw]
      - Fullerite-C50 x28,500  [raw]
      - Pyerite x76,000  [raw]
    - Methanofullerene x23,750 [reaction] (149 runs, 160/run)
      - Hydrogen Fuel Block x745 [manufacturing] (19 runs, 40/run)
        - Robotics x19  [raw]
        - Enriched Uranium x76  [raw]
        - Mechanical Parts x76  [raw]
        - Coolant x171  [raw]
        - Strontium Clathrates x380  [raw]
        - Oxygen x418  [raw]
        - Heavy Water x3,230  [raw]
        - Liquid Ozone x6,650  [raw]
        - Hydrogen Isotopes x8,550  [raw]
      - Fullerite-C70 x14,900  [raw]
      - Fullerite-C72 x14,900  [raw]
      - Isogen x44,700  [raw]
    - Lanthanum Metallofullerene x23,750 [reaction] (198 runs, 120/run)
      - Oxygen Fuel Block x990 [manufacturing] (25 runs, 40/run)
        - Robotics x25  [raw]
        - Enriched Uranium x100  [raw]
        - Mechanical Parts x100  [raw]
        - Coolant x225  [raw]
        - Strontium Clathrates x500  [raw]
        - Oxygen x550  [raw]
        - Heavy Water x4,250  [raw]
        - Liquid Ozone x8,750  [raw]
        - Oxygen Isotopes x11,250  [raw]
      - Fullerite-C70 x19,800  [raw]
      - Fullerite-C84 x19,800  [raw]
      - Nocxium x39,600  [raw]
    - C3-FTM Acid x32,500 [reaction] (325 runs, 100/run)
      - Helium Fuel Block x1,625 [manufacturing] (41 runs, 40/run)
        - Robotics x41  [raw]
        - Enriched Uranium x164  [raw]
        - Mechanical Parts x164  [raw]
        - Coolant x369  [raw]
        - Strontium Clathrates x820  [raw]
        - Oxygen x902  [raw]
        - Heavy Water x6,970  [raw]
        - Liquid Ozone x14,350  [raw]
        - Helium Isotopes x18,450  [raw]
      - Megacyte x26,000  [raw]
      - Fullerite-C84 x32,500  [raw]
      - Fullerite-C540 x32,500  [raw]
    - Carbon-86 Epoxy Resin x47,500 [reaction] (297 runs, 160/run)
      - Nitrogen Fuel Block x1,485 [manufacturing] (38 runs, 40/run)
        - Robotics x38  [raw]
        - Enriched Uranium x152  [raw]
        - Mechanical Parts x152  [raw]
        - Coolant x342  [raw]
        - Strontium Clathrates x760  [raw]
        - Oxygen x836  [raw]
        - Heavy Water x6,460  [raw]
        - Liquid Ozone x13,300  [raw]
        - Nitrogen Isotopes x17,100  [raw]
      - Zydrine x8,910  [raw]
      - Fullerite-C32 x29,700  [raw]
      - Fullerite-C320 x29,700  [raw]
    - Fullerene Intercalated Graphite x48,750 [reaction] (407 runs, 120/run)
      - Hydrogen Fuel Block x2,035 [manufacturing] (51 runs, 40/run)
        - Robotics x51  [raw]
        - Enriched Uranium x204  [raw]
        - Mechanical Parts x204  [raw]
        - Coolant x459  [raw]
        - Strontium Clathrates x1,020  [raw]
        - Oxygen x1,122  [raw]
        - Heavy Water x8,670  [raw]
        - Liquid Ozone x17,850  [raw]
        - Hydrogen Isotopes x22,950  [raw]
      - Fullerite-C60 x40,700  [raw]
      - Fullerite-C70 x40,700  [raw]
      - Mexallon x244,200  [raw]
    - Graphene Nanoribbons x70,000 [reaction] (584 runs, 120/run)
      - Nitrogen Fuel Block x2,920 [manufacturing] (73 runs, 40/run)
        - Robotics x73  [raw]
        - Enriched Uranium x292  [raw]
        - Mechanical Parts x292  [raw]
        - Coolant x657  [raw]
        - Strontium Clathrates x1,460  [raw]
        - Oxygen x1,606  [raw]
        - Heavy Water x12,410  [raw]
        - Liquid Ozone x25,550  [raw]
        - Nitrogen Isotopes x32,850  [raw]
      - Fullerite-C28 x58,400  [raw]
      - Fullerite-C32 x58,400  [raw]
      - Nocxium x233,600  [raw]
    - Plasmonic Metamaterials x70,000 [reaction] (234 runs, 300/run)
      - Hydrogen Fuel Block x1,170 [manufacturing] (30 runs, 40/run)
        - Robotics x30  [raw]
        - Enriched Uranium x120  [raw]
        - Mechanical Parts x120  [raw]
        - Coolant x270  [raw]
        - Strontium Clathrates x600  [raw]
        - Oxygen x660  [raw]
        - Heavy Water x5,100  [raw]
        - Liquid Ozone x10,500  [raw]
        - Hydrogen Isotopes x13,500  [raw]
      - Fernite Alloy x23,400 [reaction] (117 runs, 200/run)
        - Hydrogen Fuel Block x585 [manufacturing] (15 runs, 40/run)
          - Robotics x15  [raw]
          - Enriched Uranium x60  [raw]
          - Mechanical Parts x60  [raw]
          - Coolant x135  [raw]
          - Strontium Clathrates x300  [raw]
          - Oxygen x330  [raw]
          - Heavy Water x2,550  [raw]
          - Liquid Ozone x5,250  [raw]
          - Hydrogen Isotopes x6,750  [raw]
        - Scandium x11,700  [raw]
        - Vanadium x11,700  [raw]
      - Neo Mercurite x23,400 [reaction] (117 runs, 200/run)
        - Helium Fuel Block x585 [manufacturing] (15 runs, 40/run)
          - Robotics x15  [raw]
          - Enriched Uranium x60  [raw]
          - Mechanical Parts x60  [raw]
          - Coolant x135  [raw]
          - Strontium Clathrates x300  [raw]
          - Oxygen x330  [raw]
          - Heavy Water x2,550  [raw]
          - Liquid Ozone x5,250  [raw]
          - Helium Isotopes x6,750  [raw]
        - Mercury x11,700  [raw]
        - Neodymium x11,700  [raw]
    - Fulleroferrocene x82,500 [reaction] (83 runs, 1000/run)
      - Oxygen Fuel Block x415 [manufacturing] (11 runs, 40/run)
        - Robotics x11  [raw]
        - Enriched Uranium x44  [raw]
        - Mechanical Parts x44  [raw]
        - Coolant x99  [raw]
        - Strontium Clathrates x220  [raw]
        - Oxygen x242  [raw]
        - Heavy Water x1,870  [raw]
        - Liquid Ozone x3,850  [raw]
        - Oxygen Isotopes x4,950  [raw]
      - Fullerite-C60 x8,300  [raw]
      - Fullerite-C50 x16,600  [raw]
      - Tritanium x83,000  [raw]
  - Auto-Integrity Preservation Seal x800 [manufacturing] (267 runs, 3/run)
    - Supertensile Plastics x1,068  [raw]
    - Nanites x1,068  [raw]
    - Reinforced Carbon Fiber x2,670 [reaction] (14 runs, 200/run)
      - Carbon Fiber x2,800 [reaction] (14 runs, 200/run)
        - Hydrogen Fuel Block x70 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Hydrogen Isotopes x900  [raw]
        - Hydrocarbons x1,400  [raw]
        - Evaporite Deposits x1,400  [raw]
      - Oxy-Organic Solvents x14 [reaction] (2 runs, 10/run)
        - Oxygen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x4,000  [raw]
        - Atmospheric Gases x4,000  [raw]
      - Thermosetting Polymer x2,800 [reaction] (14 runs, 200/run)
        - Oxygen Fuel Block x70 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Atmospheric Gases x1,400  [raw]
        - Silicates x1,400  [raw]
  - Life Support Backup Unit x400 [manufacturing] (134 runs, 3/run)
    - Test Cultures x1,072  [raw]
    - Viral Agent x1,072  [raw]
    - Reinforced Carbon Fiber x1,340 [reaction] (7 runs, 200/run)
      - Carbon Fiber x1,400 [reaction] (7 runs, 200/run)
        - Hydrogen Fuel Block x35 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hydrocarbons x700  [raw]
        - Evaporite Deposits x700  [raw]
      - Oxy-Organic Solvents x7 [reaction] (1 runs, 10/run)
        - Oxygen Fuel Block x5 [manufacturing] (1 runs, 40/run)
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
      - Thermosetting Polymer x1,400 [reaction] (7 runs, 200/run)
        - Oxygen Fuel Block x35 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Atmospheric Gases x700  [raw]
        - Silicates x700  [raw]
  - Capital Core Temperature Regulator x10 [manufacturing] (10 runs, 1/run)
    - Integrity Response Drones x200  [raw]
    - Self-Harmonizing Power Core x200  [raw]
    - Core Temperature Regulator x350 [manufacturing] (350 runs, 1/run)
      - Chiral Structures x35,000  [raw]
      - Water x35,000  [raw]
      - Pressurized Oxidizers x175,000 [reaction] (875 runs, 200/run)
        - Carbon Polymers x175,000 [reaction] (875 runs, 200/run)
          - Helium Fuel Block x4,375 [manufacturing] (110 runs, 40/run)
            - Robotics x110  [raw]
            - Enriched Uranium x440  [raw]
            - Mechanical Parts x440  [raw]
            - Coolant x990  [raw]
            - Strontium Clathrates x2,200  [raw]
            - Oxygen x2,420  [raw]
            - Heavy Water x18,700  [raw]
            - Liquid Ozone x38,500  [raw]
            - Helium Isotopes x49,500  [raw]
          - Hydrocarbons x87,500  [raw]
          - Silicates x87,500  [raw]
        - Sulfuric Acid x175,000 [reaction] (875 runs, 200/run)
          - Nitrogen Fuel Block x4,375 [manufacturing] (110 runs, 40/run)
            - Robotics x110  [raw]
            - Enriched Uranium x440  [raw]
            - Mechanical Parts x440  [raw]
            - Coolant x990  [raw]
            - Strontium Clathrates x2,200  [raw]
            - Oxygen x2,420  [raw]
            - Heavy Water x18,700  [raw]
            - Liquid Ozone x38,500  [raw]
            - Nitrogen Isotopes x49,500  [raw]
          - Atmospheric Gases x87,500  [raw]
          - Evaporite Deposits x87,500  [raw]
        - Oxy-Organic Solvents x875 [reaction] (88 runs, 10/run)
          - Oxygen Fuel Block x440 [manufacturing] (11 runs, 40/run)
            - Robotics x11  [raw]
            - Enriched Uranium x44  [raw]
            - Mechanical Parts x44  [raw]
            - Coolant x99  [raw]
            - Strontium Clathrates x220  [raw]
            - Oxygen x242  [raw]
            - Heavy Water x1,870  [raw]
            - Liquid Ozone x3,850  [raw]
            - Oxygen Isotopes x4,950  [raw]
          - Hydrocarbons x176,000  [raw]
          - Atmospheric Gases x176,000  [raw]
      - Reinforced Carbon Fiber x175,000 [reaction] (875 runs, 200/run)
        - Carbon Fiber x175,000 [reaction] (875 runs, 200/run)
          - Hydrogen Fuel Block x4,375 [manufacturing] (110 runs, 40/run)
            - Robotics x110  [raw]
            - Enriched Uranium x440  [raw]
            - Mechanical Parts x440  [raw]
            - Coolant x990  [raw]
            - Strontium Clathrates x2,200  [raw]
            - Oxygen x2,420  [raw]
            - Heavy Water x18,700  [raw]
            - Liquid Ozone x38,500  [raw]
            - Hydrogen Isotopes x49,500  [raw]
          - Hydrocarbons x87,500  [raw]
          - Evaporite Deposits x87,500  [raw]
        - Oxy-Organic Solvents x875 [reaction] (88 runs, 10/run)
          - Oxygen Fuel Block x440 [manufacturing] (11 runs, 40/run)
            - Robotics x11  [raw]
            - Enriched Uranium x44  [raw]
            - Mechanical Parts x44  [raw]
            - Coolant x99  [raw]
            - Strontium Clathrates x220  [raw]
            - Oxygen x242  [raw]
            - Heavy Water x1,870  [raw]
            - Liquid Ozone x3,850  [raw]
            - Oxygen Isotopes x4,950  [raw]
          - Hydrocarbons x176,000  [raw]
          - Atmospheric Gases x176,000  [raw]
        - Thermosetting Polymer x175,000 [reaction] (875 runs, 200/run)
          - Oxygen Fuel Block x4,375 [manufacturing] (110 runs, 40/run)
            - Robotics x110  [raw]
            - Enriched Uranium x440  [raw]
            - Mechanical Parts x440  [raw]
            - Coolant x990  [raw]
            - Strontium Clathrates x2,200  [raw]
            - Oxygen x2,420  [raw]
            - Heavy Water x18,700  [raw]
            - Liquid Ozone x38,500  [raw]
            - Oxygen Isotopes x49,500  [raw]
          - Atmospheric Gases x87,500  [raw]
          - Silicates x87,500  [raw]
  - Enhanced Neurolink Protection Cell x1 [manufacturing] (1 runs, 1/run)
    - Counter-Subversion Sensor Array x10  [raw]
    - Nanoscale Filter Plate x10  [raw]
    - Enhanced Electro-Neural Signaller x10  [raw]
    - Neurolink Enhancer Reservoir x10 [manufacturing] (10 runs, 1/run)
      - Reinforced Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
        - Carbon Fiber x5,000 [reaction] (25 runs, 200/run)
          - Hydrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
            - Robotics x4  [raw]
            - Enriched Uranium x16  [raw]
            - Mechanical Parts x16  [raw]
            - Coolant x36  [raw]
            - Strontium Clathrates x80  [raw]
            - Oxygen x88  [raw]
            - Heavy Water x680  [raw]
            - Liquid Ozone x1,400  [raw]
            - Hydrogen Isotopes x1,800  [raw]
          - Hydrocarbons x2,500  [raw]
          - Evaporite Deposits x2,500  [raw]
        - Oxy-Organic Solvents x25 [reaction] (3 runs, 10/run)
          - Oxygen Fuel Block x15 [manufacturing] (1 runs, 40/run)
            - Robotics x1  [raw]
            - Enriched Uranium x4  [raw]
            - Mechanical Parts x4  [raw]
            - Coolant x9  [raw]
            - Strontium Clathrates x20  [raw]
            - Oxygen x22  [raw]
            - Heavy Water x170  [raw]
            - Liquid Ozone x350  [raw]
            - Oxygen Isotopes x450  [raw]
          - Hydrocarbons x6,000  [raw]
          - Atmospheric Gases x6,000  [raw]
        - Thermosetting Polymer x5,000 [reaction] (25 runs, 200/run)
          - Oxygen Fuel Block x125 [manufacturing] (4 runs, 40/run)
            - Robotics x4  [raw]
            - Enriched Uranium x16  [raw]
            - Mechanical Parts x16  [raw]
            - Coolant x36  [raw]
            - Strontium Clathrates x80  [raw]
            - Oxygen x88  [raw]
            - Heavy Water x680  [raw]
            - Liquid Ozone x1,400  [raw]
            - Oxygen Isotopes x1,800  [raw]
          - Atmospheric Gases x2,500  [raw]
          - Silicates x2,500  [raw]
      - Programmable Purification Membrane x10 [manufacturing] (10 runs, 1/run)
        - Hermetic Membranes x1,000  [raw]
        - Gel-Matrix Biopaste x3,000  [raw]
        - Morphite x15,000  [raw]
    - Nano Regulation Gate x20  [raw]
    - Genetic Safeguard Filter x75 [manufacturing] (75 runs, 1/run)
      - Genetic Lock Preserver x375 [manufacturing] (375 runs, 1/run)
        - Biocells x1,875  [raw]
        - Isotropic Neofullerene Alpha-3 x1,875 [reaction] (94 runs, 20/run)
          - Tritanium x940,000  [raw]
          - Helium Fuel Block x470 [manufacturing] (12 runs, 40/run)
            - Robotics x12  [raw]
            - Enriched Uranium x48  [raw]
            - Mechanical Parts x48  [raw]
            - Coolant x108  [raw]
            - Strontium Clathrates x240  [raw]
            - Oxygen x264  [raw]
            - Heavy Water x2,040  [raw]
            - Liquid Ozone x4,200  [raw]
            - Helium Isotopes x5,400  [raw]
          - Fullerite-C60 x47,000  [raw]
          - Fullerite-C84 x47,000  [raw]
          - Isotropic Deposition Guide x94  [raw]
      - Genetic Structure Repairer x375 [manufacturing] (375 runs, 1/run)
        - Nanites x1,875  [raw]
        - Isotropic Neofullerene Beta-6 x1,875 [reaction] (94 runs, 20/run)
          - Tritanium x940,000  [raw]
          - Hydrogen Fuel Block x470 [manufacturing] (12 runs, 40/run)
            - Robotics x12  [raw]
            - Enriched Uranium x48  [raw]
            - Mechanical Parts x48  [raw]
            - Coolant x108  [raw]
            - Strontium Clathrates x240  [raw]
            - Oxygen x264  [raw]
            - Heavy Water x2,040  [raw]
            - Liquid Ozone x4,200  [raw]
            - Hydrogen Isotopes x5,400  [raw]
          - Fullerite-C70 x47,000  [raw]
          - Fullerite-C28 x47,000  [raw]
          - Isotropic Deposition Guide x94  [raw]
      - Genetic Mutation Inhibitor x375 [manufacturing] (375 runs, 1/run)
        - Test Cultures x1,875  [raw]
        - Isotropic Neofullerene Gamma-9 x1,875 [reaction] (94 runs, 20/run)
          - Tritanium x940,000  [raw]
          - Nitrogen Fuel Block x470 [manufacturing] (12 runs, 40/run)
            - Robotics x12  [raw]
            - Enriched Uranium x48  [raw]
            - Mechanical Parts x48  [raw]
            - Coolant x108  [raw]
            - Strontium Clathrates x240  [raw]
            - Oxygen x264  [raw]
            - Heavy Water x2,040  [raw]
            - Liquid Ozone x4,200  [raw]
            - Nitrogen Isotopes x5,400  [raw]
          - Fullerite-C50 x47,000  [raw]
          - Fullerite-C72 x47,000  [raw]
          - Isotropic Deposition Guide x94  [raw]
    - Meta-Operant Neurolink Enhancer x150 [reaction] (8 runs, 20/run)
      - Meta-Molecular Combiner x8  [raw]
      - Hydrogen Fuel Block x40 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Hypnagogic Neurolink Enhancer x640 [reaction] (32 runs, 20/run)
        - Helium Fuel Block x160 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Helium Isotopes x1,800  [raw]
        - Lime Mykoserocin x1,280  [raw]
        - Malachite Mykoserocin x1,280  [raw]
        - LM-Composite Molecular Condenser x32  [raw]
      - Axosomatic Neurolink Enhancer x640 [reaction] (32 runs, 20/run)
        - Nitrogen Fuel Block x160 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Nitrogen Isotopes x1,800  [raw]
        - Amber Mykoserocin x1,280  [raw]
        - Golden Mykoserocin x1,280  [raw]
        - AG-Composite Molecular Condenser x32  [raw]
      - Cogni-Emotive Neurolink Enhancer x640 [reaction] (32 runs, 20/run)
        - Oxygen Fuel Block x160 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Celadon Mykoserocin x1,280  [raw]
        - Viridian Mykoserocin x1,280  [raw]
        - CV-Composite Molecular Condenser x32  [raw]
      - Sense-Heuristic Neurolink Enhancer x640 [reaction] (32 runs, 20/run)
        - Hydrogen Fuel Block x160 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Azure Mykoserocin x1,280  [raw]
        - Vermillion Mykoserocin x1,280  [raw]
        - AV-Composite Molecular Condenser x32  [raw]
    - Synthetic Synapses x3,000  [raw]
    - Miniature Electronics x15,000  [raw]
```

## Aggregated phases (shared intermediates merged)

### Phase 6

| Type | Required | Activity / runs |
|---|---:|---|
| Hel | 1 | manufacturing, 1 runs |

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Capital Propulsion Engine | 50 | manufacturing, 50 runs |
| Capital Sensor Cluster | 40 | manufacturing, 40 runs |
| Capital Armor Plates | 50 | manufacturing, 50 runs |
| Capital Capacitor Battery | 150 | manufacturing, 150 runs |
| Capital Power Generator | 50 | manufacturing, 50 runs |
| Capital Shield Emitter | 100 | manufacturing, 100 runs |
| Capital Jump Drive | 100 | manufacturing, 100 runs |
| Capital Drone Bay | 250 | manufacturing, 250 runs |
| Capital Computer System | 10 | manufacturing, 10 runs |
| Capital Construction Parts | 50 | manufacturing, 50 runs |
| Capital Ship Maintenance Bay | 100 | manufacturing, 100 runs |
| Capital Corporate Hangar Bay | 50 | manufacturing, 50 runs |
| G-O Trigger Neurolink Conduit | 64 | manufacturing, 64 runs |
| Ladar-FTL Interlink Communicator | 125 | manufacturing, 125 runs |
| Auto-Integrity Preservation Seal | 800 | manufacturing, 267 runs |
| Life Support Backup Unit | 400 | manufacturing, 134 runs |
| Capital Core Temperature Regulator | 10 | manufacturing, 10 runs |
| Enhanced Neurolink Protection Cell | 1 | manufacturing, 1 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Self-Harmonizing Power Core | 575 | raw (terminator) |
| Megacyte | 286,050 | raw (terminator) |
| Zydrine | 574,000 | raw (terminator) |
| Nocxium | 1,136,300 | raw (terminator) |
| Isogen | 11,437,500 | raw (terminator) |
| Tritanium | 40,818,750 | raw (terminator) |
| Mexallon | 40,818,750 | raw (terminator) |
| Pyerite | 146,737,500 | raw (terminator) |
| Broadcast Node | 540 | raw (terminator) |
| Organic Mortar Applicators | 250 | raw (terminator) |
| Recursive Computing Module | 110 | raw (terminator) |
| Wetware Mainframe | 225 | raw (terminator) |
| Integrity Response Drones | 300 | raw (terminator) |
| Supertensile Plastics | 1,068 | raw (terminator) |
| Nanites | 1,068 | raw (terminator) |
| Test Cultures | 1,072 | raw (terminator) |
| Viral Agent | 1,072 | raw (terminator) |
| Counter-Subversion Sensor Array | 10 | raw (terminator) |
| Nanoscale Filter Plate | 10 | raw (terminator) |
| Enhanced Electro-Neural Signaller | 10 | raw (terminator) |
| Nano Regulation Gate | 20 | raw (terminator) |
| Synthetic Synapses | 3,000 | raw (terminator) |
| Miniature Electronics | 15,000 | raw (terminator) |
| Fermionic Condensates | 5,000 | reaction, 25 runs |
| Fulleroferrocene | 82,500 | reaction, 83 runs |
| PPD Fullerene Fibers | 23,750 | reaction, 95 runs |
| Fullerene Intercalated Graphite | 48,750 | reaction, 407 runs |
| Methanofullerene | 23,750 | reaction, 149 runs |
| Lanthanum Metallofullerene | 23,750 | reaction, 198 runs |
| Scandium Metallofullerene | 16,250 | reaction, 102 runs |
| Graphene Nanoribbons | 70,000 | reaction, 584 runs |
| Carbon-86 Epoxy Resin | 47,500 | reaction, 297 runs |
| C3-FTM Acid | 32,500 | reaction, 325 runs |
| Plasmonic Metamaterials | 70,000 | reaction, 234 runs |
| Pressurized Oxidizers | 640 | reaction, 4 runs |
| Reinforced Carbon Fiber | 104,650 | reaction, 524 runs |
| Meta-Operant Neurolink Enhancer | 150 | reaction, 8 runs |
| Sense-Heuristic Neurolink Enhancer | 2,560 | reaction, 128 runs |
| Goal-Orienting Neurolink Stabilizer | 64 | reaction, 7 runs |
| Core Temperature Regulator | 350 | manufacturing, 350 runs |
| Genetic Safeguard Filter | 75 | manufacturing, 75 runs |
| Neurolink Enhancer Reservoir | 10 | manufacturing, 10 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Azure Mykoserocin | 5,120 | raw (terminator) |
| Vermillion Mykoserocin | 5,120 | raw (terminator) |
| AV-Composite Molecular Condenser | 135 | raw (terminator) |
| Vermillion Cytoserocin | 70 | raw (terminator) |
| Azure Cytoserocin | 70 | raw (terminator) |
| Zydrine | 11,460 | raw (terminator) |
| Fullerite-C72 | 25,100 | raw (terminator) |
| Fullerite-C28 | 68,600 | raw (terminator) |
| Fullerite-C60 | 58,500 | raw (terminator) |
| Fullerite-C50 | 45,100 | raw (terminator) |
| Pyerite | 76,000 | raw (terminator) |
| Fullerite-C70 | 75,400 | raw (terminator) |
| Isogen | 44,700 | raw (terminator) |
| Fullerite-C84 | 52,300 | raw (terminator) |
| Nocxium | 273,200 | raw (terminator) |
| Megacyte | 26,000 | raw (terminator) |
| Fullerite-C540 | 32,500 | raw (terminator) |
| Fullerite-C32 | 88,100 | raw (terminator) |
| Fullerite-C320 | 29,700 | raw (terminator) |
| Mexallon | 244,200 | raw (terminator) |
| Tritanium | 83,000 | raw (terminator) |
| Chiral Structures | 35,000 | raw (terminator) |
| Water | 35,000 | raw (terminator) |
| Meta-Molecular Combiner | 8 | raw (terminator) |
| Nitrogen Fuel Block | 4,405 | manufacturing, 111 runs |
| Hydrogen Fuel Block | 5,140 | manufacturing, 129 runs |
| Helium Fuel Block | 2,260 | manufacturing, 57 runs |
| Oxygen Fuel Block | 1,405 | manufacturing, 36 runs |
| Fernite Alloy | 23,400 | reaction, 117 runs |
| Carbon Polymers | 800 | reaction, 4 runs |
| Sulfuric Acid | 800 | reaction, 4 runs |
| Caesarium Cadmide | 2,500 | reaction, 13 runs |
| Neo Mercurite | 23,400 | reaction, 117 runs |
| Dysporite | 2,500 | reaction, 13 runs |
| Fluxed Condensates | 2,500 | reaction, 13 runs |
| Prometium | 2,500 | reaction, 13 runs |
| Carbon Fiber | 104,800 | reaction, 524 runs |
| Oxy-Organic Solvents | 528 | reaction, 53 runs |
| Thermosetting Polymer | 104,800 | reaction, 524 runs |
| Pressurized Oxidizers | 175,000 | reaction, 875 runs |
| Reinforced Carbon Fiber | 180,000 | reaction, 900 runs |
| Hypnagogic Neurolink Enhancer | 640 | reaction, 32 runs |
| Axosomatic Neurolink Enhancer | 640 | reaction, 32 runs |
| Cogni-Emotive Neurolink Enhancer | 640 | reaction, 32 runs |
| Sense-Heuristic Neurolink Enhancer | 640 | reaction, 32 runs |
| Programmable Purification Membrane | 10 | manufacturing, 10 runs |
| Genetic Lock Preserver | 375 | manufacturing, 375 runs |
| Genetic Structure Repairer | 375 | manufacturing, 375 runs |
| Genetic Mutation Inhibitor | 375 | manufacturing, 375 runs |

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrocarbons | 158,800 | raw (terminator) |
| Evaporite Deposits | 52,800 | raw (terminator) |
| Atmospheric Gases | 158,800 | raw (terminator) |
| Silicates | 52,800 | raw (terminator) |
| Robotics | 333 | raw (terminator) |
| Enriched Uranium | 1,332 | raw (terminator) |
| Mechanical Parts | 1,332 | raw (terminator) |
| Coolant | 2,997 | raw (terminator) |
| Strontium Clathrates | 6,660 | raw (terminator) |
| Oxygen | 7,326 | raw (terminator) |
| Heavy Water | 56,610 | raw (terminator) |
| Liquid Ozone | 116,550 | raw (terminator) |
| Hydrogen Isotopes | 58,050 | raw (terminator) |
| Helium Isotopes | 25,650 | raw (terminator) |
| Cadmium | 2,600 | raw (terminator) |
| Caesium | 1,300 | raw (terminator) |
| Mercury | 13,000 | raw (terminator) |
| Dysprosium | 1,300 | raw (terminator) |
| Neodymium | 13,000 | raw (terminator) |
| Thulium | 1,300 | raw (terminator) |
| Promethium | 1,300 | raw (terminator) |
| Oxygen Isotopes | 16,200 | raw (terminator) |
| Nitrogen Isotopes | 49,950 | raw (terminator) |
| Scandium | 11,700 | raw (terminator) |
| Vanadium | 11,700 | raw (terminator) |
| Hermetic Membranes | 1,000 | raw (terminator) |
| Gel-Matrix Biopaste | 3,000 | raw (terminator) |
| Morphite | 15,000 | raw (terminator) |
| Biocells | 1,875 | raw (terminator) |
| Nanites | 1,875 | raw (terminator) |
| Test Cultures | 1,875 | raw (terminator) |
| Lime Mykoserocin | 1,280 | raw (terminator) |
| Malachite Mykoserocin | 1,280 | raw (terminator) |
| LM-Composite Molecular Condenser | 32 | raw (terminator) |
| Amber Mykoserocin | 1,280 | raw (terminator) |
| Golden Mykoserocin | 1,280 | raw (terminator) |
| AG-Composite Molecular Condenser | 32 | raw (terminator) |
| Celadon Mykoserocin | 1,280 | raw (terminator) |
| Viridian Mykoserocin | 1,280 | raw (terminator) |
| CV-Composite Molecular Condenser | 32 | raw (terminator) |
| Azure Mykoserocin | 1,280 | raw (terminator) |
| Vermillion Mykoserocin | 1,280 | raw (terminator) |
| AV-Composite Molecular Condenser | 32 | raw (terminator) |
| Nitrogen Fuel Block | 180 | manufacturing, 5 runs |
| Hydrogen Fuel Block | 3,365 | manufacturing, 85 runs |
| Helium Fuel Block | 830 | manufacturing, 21 runs |
| Oxygen Fuel Block | 3,240 | manufacturing, 81 runs |
| Carbon Polymers | 175,000 | reaction, 875 runs |
| Sulfuric Acid | 175,000 | reaction, 875 runs |
| Carbon Fiber | 180,000 | reaction, 900 runs |
| Oxy-Organic Solvents | 1,775 | reaction, 178 runs |
| Thermosetting Polymer | 180,000 | reaction, 900 runs |
| Isotropic Neofullerene Alpha-3 | 1,875 | reaction, 94 runs |
| Isotropic Neofullerene Beta-6 | 1,875 | reaction, 94 runs |
| Isotropic Neofullerene Gamma-9 | 1,875 | reaction, 94 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 192 | raw (terminator) |
| Enriched Uranium | 768 | raw (terminator) |
| Mechanical Parts | 768 | raw (terminator) |
| Coolant | 1,728 | raw (terminator) |
| Strontium Clathrates | 3,840 | raw (terminator) |
| Oxygen | 4,224 | raw (terminator) |
| Heavy Water | 32,640 | raw (terminator) |
| Liquid Ozone | 67,200 | raw (terminator) |
| Hydrogen Isotopes | 38,250 | raw (terminator) |
| Oxygen Isotopes | 36,450 | raw (terminator) |
| Helium Isotopes | 9,450 | raw (terminator) |
| Nitrogen Isotopes | 2,250 | raw (terminator) |
| Hydrocarbons | 533,500 | raw (terminator) |
| Silicates | 177,500 | raw (terminator) |
| Atmospheric Gases | 533,500 | raw (terminator) |
| Evaporite Deposits | 177,500 | raw (terminator) |
| Tritanium | 2,820,000 | raw (terminator) |
| Fullerite-C60 | 47,000 | raw (terminator) |
| Fullerite-C84 | 47,000 | raw (terminator) |
| Isotropic Deposition Guide | 282 | raw (terminator) |
| Fullerite-C70 | 47,000 | raw (terminator) |
| Fullerite-C28 | 47,000 | raw (terminator) |
| Fullerite-C50 | 47,000 | raw (terminator) |
| Fullerite-C72 | 47,000 | raw (terminator) |
| Nitrogen Fuel Block | 4,845 | manufacturing, 122 runs |
| Hydrogen Fuel Block | 4,970 | manufacturing, 125 runs |
| Helium Fuel Block | 4,845 | manufacturing, 122 runs |
| Oxygen Fuel Block | 5,390 | manufacturing, 135 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 504 | raw (terminator) |
| Enriched Uranium | 2,016 | raw (terminator) |
| Mechanical Parts | 2,016 | raw (terminator) |
| Coolant | 4,536 | raw (terminator) |
| Strontium Clathrates | 10,080 | raw (terminator) |
| Oxygen | 11,088 | raw (terminator) |
| Heavy Water | 85,680 | raw (terminator) |
| Liquid Ozone | 176,400 | raw (terminator) |
| Helium Isotopes | 54,900 | raw (terminator) |
| Nitrogen Isotopes | 54,900 | raw (terminator) |
| Oxygen Isotopes | 60,750 | raw (terminator) |
| Hydrogen Isotopes | 56,250 | raw (terminator) |

## Raw-material acquisition table (Hel ×1)

| Mineral | Required |
|---|---:|
| Pyerite | 146,813,500 |
| Tritanium | 43,721,750 |
| Mexallon | 41,062,950 |
| Isogen | 11,482,200 |
| Nocxium | 1,409,500 |
| Zydrine | 585,460 |
| Megacyte | 312,050 |

| Moon material | Required |
|---|---:|
| Hydrocarbons | 692,300 |
| Atmospheric Gases | 692,300 |
| Silicates | 230,300 |
| Evaporite Deposits | 230,300 |
| Morphite | 15,000 |
| Mercury | 13,000 |
| Neodymium | 13,000 |
| Vanadium | 11,700 |
| Scandium | 11,700 |
| Cadmium | 2,600 |
| Caesium | 1,300 |
| Dysprosium | 1,300 |
| Promethium | 1,300 |
| Thulium | 1,300 |

| PI commodity | Required |
|---|---:|
| Chiral Structures | 35,000 |
| Water | 35,000 |
| Miniature Electronics | 15,000 |
| Coolant | 9,261 |
| Enriched Uranium | 4,116 |
| Mechanical Parts | 4,116 |
| Synthetic Synapses | 3,000 |
| Gel-Matrix Biopaste | 3,000 |
| Test Cultures | 2,947 |
| Nanites | 2,943 |
| Biocells | 1,875 |
| Viral Agent | 1,072 |
| Supertensile Plastics | 1,068 |
| Robotics | 1,029 |
| Hermetic Membranes | 1,000 |
| Self-Harmonizing Power Core | 575 |
| Broadcast Node | 540 |
| Integrity Response Drones | 300 |
| Organic Mortar Applicators | 250 |
| Wetware Mainframe | 225 |
| Recursive Computing Module | 110 |

| Ice product | Required |
|---|---:|
| Liquid Ozone | 360,150 |
| Heavy Water | 174,930 |
| Hydrogen Isotopes | 152,550 |
| Oxygen Isotopes | 113,400 |
| Nitrogen Isotopes | 107,100 |
| Helium Isotopes | 90,000 |
| Oxygen | 22,638 |
| Strontium Clathrates | 20,580 |

| Gas (harvestable clouds) | Required |
|---|---:|
| Fullerite-C70 | 122,400 |
| Fullerite-C28 | 115,600 |
| Fullerite-C60 | 105,500 |
| Fullerite-C84 | 99,300 |
| Fullerite-C50 | 92,100 |
| Fullerite-C32 | 88,100 |
| Fullerite-C72 | 72,100 |
| Fullerite-C540 | 32,500 |
| Fullerite-C320 | 29,700 |
| Azure Mykoserocin | 6,400 |
| Vermillion Mykoserocin | 6,400 |
| Amber Mykoserocin | 1,280 |
| Golden Mykoserocin | 1,280 |
| Lime Mykoserocin | 1,280 |
| Malachite Mykoserocin | 1,280 |
| Celadon Mykoserocin | 1,280 |
| Viridian Mykoserocin | 1,280 |
| Azure Cytoserocin | 70 |
| Vermillion Cytoserocin | 70 |

| NPC market good | Required |
|---|---:|
| Isotropic Deposition Guide | 282 |
| AV-Composite Molecular Condenser | 167 |
| AG-Composite Molecular Condenser | 32 |
| LM-Composite Molecular Condenser | 32 |
| CV-Composite Molecular Condenser | 32 |
| Nano Regulation Gate | 20 |
| Counter-Subversion Sensor Array | 10 |
| Nanoscale Filter Plate | 10 |
| Enhanced Electro-Neural Signaller | 10 |
| Meta-Molecular Combiner | 8 |

## Blueprint inventory (live, 2026-11-21)

79 blueprint types — **44 owned, 35 missing** (23 blueprints +
12 reaction formulas).

Owned (the Charon/Typhoon world carries over, plus surprises):

| Blueprint | Family |
|---|---|
| Auto-Integrity Preservation Seal · Life Support Backup Unit · Core Temperature Regulator | capital-adjacent components (the Typhoon world) |
| Nitrogen / Hydrogen / Helium / Oxygen Fuel Block | fuel blocks |
| Carbon Fiber · Carbon Polymers · Sulfuric Acid · Oxy-Organic Solvents · Pressurized Oxidizers · Reinforced Carbon Fiber · Thermosetting Polymer | simple reaction formulas |
| PPD Fullerene Fibers · Fullerene Intercalated Graphite · Methanofullerene · Lanthanum Metallofullerene · Scandium Metallofullerene · Graphene Nanoribbons · Carbon-86 Epoxy Resin · C3-FTM Acid · Fulleroferrocene | polymer formulas (the Jackdaw world) |
| Isotropic Neofullerene Alpha-3 / Beta-6 / Gamma-9 · Sense-Heuristic Neurolink Enhancer · Goal-Orienting Neurolink Stabilizer | **neurolink formulas the roster already holds** — live line evidence of prior neurolink production |

Missing — capital & supercapital components (23 blueprints, NPC-seeded originals per the Panther precedent):

| Blueprint | Notes |
|---|---|
| Capital Propulsion Engine · Capital Sensor Cluster · Capital Armor Plates · Capital Capacitor Battery · Capital Power Generator · Capital Shield Emitter · Capital Jump Drive · Capital Drone Bay · Capital Computer System · Capital Construction Parts · Capital Ship Maintenance Bay · Capital Corporate Hangar Bay · Capital Core Temperature Regulator | the Charon's component set, ~10× its bill |
| Ladar-FTL Interlink Communicator · G-O Trigger Neurolink Conduit · Enhanced Neurolink Protection Cell | supercapital-specific |
| Neurolink Enhancer Reservoir · Genetic Safeguard Filter · Genetic Lock Preserver · Genetic Structure Repairer · Genetic Mutation Inhibitor · Programmable Purification Membrane | neurolink support components |
| **Hel Blueprint** | **contract** — no BPC source in the SDE (rare-drop origin, pin; verify against M15 contract data) |

Missing — reaction formulas (12, NPC-seeded originals): Fermionic
Condensates · Plasmonic Metamaterials · Dysporite · Prometium ·
Fluxed Condensates · Caesarium Cadmide · Neo Mercurite · Fernite
Alloy · Hypnagogic / Axosomatic / Cogni-Emotive / Meta-Operant
Neurolink Enhancer formulas.

## Mechanics the expansion established

- **Three chains converge in one**: the Hel walk nests the Charon
  (capital components, PI tier-4, advanced composites), the Jackdaw
  (fullerene polymers off w-space gases), and the Panther (advanced
  reactions) at multiplied scale, then adds the neurolink family on
  top. For M5 this is the strongest resolver stress yet — 79
  commodities, 7 levels, every activity type in one chain — and the
  strongest aggregation case: shared intermediates (fuel blocks,
  RCF, Carbon Fiber) recur at 2-3 levels each with large merge
  savings.
- **The reaction layer is the industrial era**: 10,478 runs × 3 h =
  31,434 slot-hours — at the roster's full reaction concurrency
  (~10 slots) that is still **131 days of reactions**, dwarfing the
  47-day hull build. A single character's reaction slots are the
  hard bottleneck; the plan is months long however it schedules,
  and reaction-slot count is the throughput asset (formulas are
  cheap; slots are not).
- **maxPL 1 + BPC-only acquisition**: the hull's BPC arrives by
  contract (rare-drop origin), builds exactly one ship, and cannot
  be copied into parallelism. The acquisition tier for the target
  itself is a single contract purchase — the simplest target
  acquisition in the program, on the most expensive item.
- **Recurring commodities define the schedule**: with seven
  commodity types recurring at 2-3 phase levels, the
  merged-campaign decision (M5/M9) moves from optimization to
  necessity — per-phase campaigns at this scale would duplicate
  thousands of runs of fuel-block and carbon-family production.
- **Neurolink is a new sub-world**: molecular-forged reactions over
  k-space gases (the full mykoserocin/cytoserocin family — 15 gas
  terminators in this chain), NPC molecular-forging tools (five
  more 'Commodities' catch-all members), and PI tiers 2-4 — a
  compact echo of the whole reaction world inside three components.

## Findings and caveats

- **Wave shape**: the hull build (47.2 d skilled) plus the reaction
  stack (131 d at ~10 slots) make this a **months-long plan** — the
  first where the mockup's wave bar must compress to a readable
  scale, and where slot count, not blueprint count, is the wall.
- **The skill gap is the story**: Capital Ship Construction 4 vs
  Octavia's level 1 — a 3-level, ~2-month train before the hull can
  install at all, with component work fillable meanwhile. The
  skill-plan calculator TODO item (multi-character fastest-path)
  was recorded for exactly this shape.
- **The one covered mineral**: Tritanium (97.4M on hand against
  43.7M needed) — everything else in the mineral mountain is a
  purchase or mining campaign measured in hundreds of millions of
  ISK.
- **Prior-line evidence**: the roster already holds three neurolink
  formulas and the Isotropic Neofullerene set — someone built
  neurolink components before; the live line has history here even
  though nothing super-relevant is stocked.
- Pins: the Hel BPC's drop source (M15 contract verification), the
  supercapital facility class for M3 (structure-only build,
  community-documented), and reaction-slot semantics at scale (the
  standing M4/M9 pin — this chain makes it the binding constraint).
