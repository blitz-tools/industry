# The Ragnarok chain — full reference

Tenth chain document (after `TYPHOON-CHAIN.md` through
`TFI-CHAIN.md`), added 2026-11-21 for the **absolute chain stress
test** — the roadmap's final chain set: the Ragnarok Minmatar titan
×1. The Hel's convergence world at roughly four times its bill,
plus four titan-specific components and the longest build in the
program by half again. Every program record falls: **82 buildable
commodities, 11,728 manufacturing runs, 27,979 reaction runs**
(83,937 slot-hours), 82 raw types, and a **1.117-billion-Pyerite
mineral mountain** — 7.6× the Hel's. Every deterministic number
here is output of the reference scripts — regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 23773 1
```

Provenance: read from the live SDE (Static Data Export) mirror
(release 2026-11-20) and the synced live tables (ownership, skills,
stock — 2026-11-21). Phases count up in build order (terminators =
phase 0, target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Ragnarok ×1)

- IDs: Ragnarok **23773**, Blueprint **23774** (maxProductionLimit
  **1**, 9,000,000 s build — **104.2 d unskilled, 70.8 d at the
  max-skills 0.68 multiplier**: half again the Hel's record). Copy
  activity exists (7.2M s) but is moot — the BPC is contract-only
  (no SDE source, rare-drop origin; **pin, verify against M15
  contract data** — the Hel's pin carried over).
- **21 hull materials** — the Hel's 18 at ~4× the bill (AIPS ×3,200
  = 1,067 runs · LSBU ×1,600 = 534 runs · fourteen capital
  components at 2.5–5× their Hel quantities), **plus four
  titan-specific components**: Capital Jump Bridge Array ×500,
  Capital Clone Vat Bay ×500, Capital Doomsday Weapon Mount ×500,
  Capital Turret Hardpoint ×400 — all **mineral-heavy builds**
  (millions of Pyerite each) that add volume rather than reaction
  depth. The neurolink trio returns at 1.5–3× (G-O Trigger ×192,
  Ladar-FTL ×250, Enhanced Protection Cell ×1).
- **Scale by the numbers**: 7 buildable phases (the Hel's depth)
  · **82 buildable commodities** · 11,728 manufacturing runs ·
  **27,979 reaction runs = 83,937 slot-hours** (3,497 d
  single-slot — nearly 10 years; at ~10 parallel reactors,
  **350 days of reactions alone**) · 1,192 fuel-block runs ·
  **82 raw types** — every number a program record.
- **The mineral mountain, final form**: Pyerite **1.117 billion**,
  Tritanium 318.8M, Mexallon 300.7M, Isogen 84.7M — 7.6× the
  Hel's bill and roughly 1,700× current stock. The largest
  material procurement conceivable in the program.
- **Recurring commodities at maximum**: every fuel-block type at
  three levels, RCF at two (2,555 + 2,213 runs), Carbon Fiber at
  two (2,555 + 2,213), Thermosetting Polymer at two, Pressurized
  Oxidizers at two (10 + 2,188) — the merged-campaign question's
  terminal case: per-phase campaigns would duplicate tens of
  thousands of runs.
- Skills: **Capital Ship Construction 5** gates the hull (held at
  level **1** by Octavia Arbitrage, the sole holder — a 4-level,
  ~4-month gap, the skill-plan calculator's stress case).
  Reaction tiers per the component families (held); the titan
  components themselves gate on Industry 1.
- **Blueprint inventory: 82 types — 44 owned, 38 missing**. The
  owned set is identical to the Hel's (the prior worlds carried
  over wholesale). Missing: the Hel's 35 plus **four titan
  component BPs** (Jump Bridge Array, Clone Vat Bay, Doomsday
  Weapon Mount, Turret Hardpoint — NPC-seeded originals).
- **From zero on everything titan-relevant**: no BPC, no titan
  component BPs, and the mineral mountain dwarfs holdings
  (Tritanium 97.4M on hand against 318.8M — 30% covered; every
  other mineral ≈0%).
- **Structure-only build** — the supercapital assembly pin (M3)
  carried over from the Hel; titans need the same facility class.

## Per-branch tree (Ragnarok ×1)

```text
- Ragnarok x1 [manufacturing] (1 runs, 1/run)
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
  - Capital Core Temperature Regulator x25 [manufacturing] (25 runs, 1/run)
    - Integrity Response Drones x500  [raw]
    - Self-Harmonizing Power Core x500  [raw]
    - Core Temperature Regulator x875 [manufacturing] (875 runs, 1/run)
      - Chiral Structures x87,500  [raw]
      - Water x87,500  [raw]
      - Pressurized Oxidizers x437,500 [reaction] (2,188 runs, 200/run)
        - Carbon Polymers x437,600 [reaction] (2,188 runs, 200/run)
          - Helium Fuel Block x10,940 [manufacturing] (274 runs, 40/run)
            - Robotics x274  [raw]
            - Enriched Uranium x1,096  [raw]
            - Mechanical Parts x1,096  [raw]
            - Coolant x2,466  [raw]
            - Strontium Clathrates x5,480  [raw]
            - Oxygen x6,028  [raw]
            - Heavy Water x46,580  [raw]
            - Liquid Ozone x95,900  [raw]
            - Helium Isotopes x123,300  [raw]
          - Hydrocarbons x218,800  [raw]
          - Silicates x218,800  [raw]
        - Sulfuric Acid x437,600 [reaction] (2,188 runs, 200/run)
          - Nitrogen Fuel Block x10,940 [manufacturing] (274 runs, 40/run)
            - Robotics x274  [raw]
            - Enriched Uranium x1,096  [raw]
            - Mechanical Parts x1,096  [raw]
            - Coolant x2,466  [raw]
            - Strontium Clathrates x5,480  [raw]
            - Oxygen x6,028  [raw]
            - Heavy Water x46,580  [raw]
            - Liquid Ozone x95,900  [raw]
            - Nitrogen Isotopes x123,300  [raw]
          - Atmospheric Gases x218,800  [raw]
          - Evaporite Deposits x218,800  [raw]
        - Oxy-Organic Solvents x2,188 [reaction] (219 runs, 10/run)
          - Oxygen Fuel Block x1,095 [manufacturing] (28 runs, 40/run)
            - Robotics x28  [raw]
            - Enriched Uranium x112  [raw]
            - Mechanical Parts x112  [raw]
            - Coolant x252  [raw]
            - Strontium Clathrates x560  [raw]
            - Oxygen x616  [raw]
            - Heavy Water x4,760  [raw]
            - Liquid Ozone x9,800  [raw]
            - Oxygen Isotopes x12,600  [raw]
          - Hydrocarbons x438,000  [raw]
          - Atmospheric Gases x438,000  [raw]
      - Reinforced Carbon Fiber x437,500 [reaction] (2,188 runs, 200/run)
        - Carbon Fiber x437,600 [reaction] (2,188 runs, 200/run)
          - Hydrogen Fuel Block x10,940 [manufacturing] (274 runs, 40/run)
            - Robotics x274  [raw]
            - Enriched Uranium x1,096  [raw]
            - Mechanical Parts x1,096  [raw]
            - Coolant x2,466  [raw]
            - Strontium Clathrates x5,480  [raw]
            - Oxygen x6,028  [raw]
            - Heavy Water x46,580  [raw]
            - Liquid Ozone x95,900  [raw]
            - Hydrogen Isotopes x123,300  [raw]
          - Hydrocarbons x218,800  [raw]
          - Evaporite Deposits x218,800  [raw]
        - Oxy-Organic Solvents x2,188 [reaction] (219 runs, 10/run)
          - Oxygen Fuel Block x1,095 [manufacturing] (28 runs, 40/run)
            - Robotics x28  [raw]
            - Enriched Uranium x112  [raw]
            - Mechanical Parts x112  [raw]
            - Coolant x252  [raw]
            - Strontium Clathrates x560  [raw]
            - Oxygen x616  [raw]
            - Heavy Water x4,760  [raw]
            - Liquid Ozone x9,800  [raw]
            - Oxygen Isotopes x12,600  [raw]
          - Hydrocarbons x438,000  [raw]
          - Atmospheric Gases x438,000  [raw]
        - Thermosetting Polymer x437,600 [reaction] (2,188 runs, 200/run)
          - Oxygen Fuel Block x10,940 [manufacturing] (274 runs, 40/run)
            - Robotics x274  [raw]
            - Enriched Uranium x1,096  [raw]
            - Mechanical Parts x1,096  [raw]
            - Coolant x2,466  [raw]
            - Strontium Clathrates x5,480  [raw]
            - Oxygen x6,028  [raw]
            - Heavy Water x46,580  [raw]
            - Liquid Ozone x95,900  [raw]
            - Oxygen Isotopes x123,300  [raw]
          - Atmospheric Gases x218,800  [raw]
          - Silicates x218,800  [raw]
  - Capital Propulsion Engine x80 [manufacturing] (80 runs, 1/run)
    - Self-Harmonizing Power Core x80  [raw]
    - Reinforced Carbon Fiber x8,000 [reaction] (40 runs, 200/run)
      - Carbon Fiber x8,000 [reaction] (40 runs, 200/run)
        - Hydrogen Fuel Block x200 [manufacturing] (5 runs, 40/run)
          - Robotics x5  [raw]
          - Enriched Uranium x20  [raw]
          - Mechanical Parts x20  [raw]
          - Coolant x45  [raw]
          - Strontium Clathrates x100  [raw]
          - Oxygen x110  [raw]
          - Heavy Water x850  [raw]
          - Liquid Ozone x1,750  [raw]
          - Hydrogen Isotopes x2,250  [raw]
        - Hydrocarbons x4,000  [raw]
        - Evaporite Deposits x4,000  [raw]
      - Oxy-Organic Solvents x40 [reaction] (4 runs, 10/run)
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
        - Hydrocarbons x8,000  [raw]
        - Atmospheric Gases x8,000  [raw]
      - Thermosetting Polymer x8,000 [reaction] (40 runs, 200/run)
        - Oxygen Fuel Block x200 [manufacturing] (5 runs, 40/run)
          - Robotics x5  [raw]
          - Enriched Uranium x20  [raw]
          - Mechanical Parts x20  [raw]
          - Coolant x45  [raw]
          - Strontium Clathrates x100  [raw]
          - Oxygen x110  [raw]
          - Heavy Water x850  [raw]
          - Liquid Ozone x1,750  [raw]
          - Oxygen Isotopes x2,250  [raw]
        - Atmospheric Gases x4,000  [raw]
        - Silicates x4,000  [raw]
    - Megacyte x22,800  [raw]
    - Zydrine x45,600  [raw]
    - Nocxium x90,000  [raw]
    - Isogen x900,000  [raw]
    - Tritanium x3,240,000  [raw]
    - Mexallon x3,240,000  [raw]
    - Pyerite x11,700,000  [raw]
  - Capital Sensor Cluster x100 [manufacturing] (100 runs, 1/run)
    - Broadcast Node x100  [raw]
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
    - Megacyte x28,500  [raw]
    - Zydrine x57,000  [raw]
    - Nocxium x112,500  [raw]
    - Isogen x1,125,000  [raw]
    - Tritanium x4,050,000  [raw]
    - Mexallon x4,050,000  [raw]
    - Pyerite x14,625,000  [raw]
  - Capital Shield Emitter x150 [manufacturing] (150 runs, 1/run)
    - Recursive Computing Module x150  [raw]
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
    - Megacyte x46,200  [raw]
    - Zydrine x92,250  [raw]
    - Nocxium x180,000  [raw]
    - Isogen x1,800,000  [raw]
    - Tritanium x6,750,000  [raw]
    - Mexallon x6,750,000  [raw]
    - Pyerite x23,625,000  [raw]
  - G-O Trigger Neurolink Conduit x192 [manufacturing] (192 runs, 1/run)
    - Pressurized Oxidizers x1,920 [reaction] (10 runs, 200/run)
      - Carbon Polymers x2,000 [reaction] (10 runs, 200/run)
        - Helium Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Helium Isotopes x900  [raw]
        - Hydrocarbons x1,000  [raw]
        - Silicates x1,000  [raw]
      - Sulfuric Acid x2,000 [reaction] (10 runs, 200/run)
        - Nitrogen Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Nitrogen Isotopes x900  [raw]
        - Atmospheric Gases x1,000  [raw]
        - Evaporite Deposits x1,000  [raw]
      - Oxy-Organic Solvents x10 [reaction] (1 runs, 10/run)
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
    - Reinforced Carbon Fiber x1,920 [reaction] (10 runs, 200/run)
      - Carbon Fiber x2,000 [reaction] (10 runs, 200/run)
        - Hydrogen Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Hydrogen Isotopes x900  [raw]
        - Hydrocarbons x1,000  [raw]
        - Evaporite Deposits x1,000  [raw]
      - Oxy-Organic Solvents x10 [reaction] (1 runs, 10/run)
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
      - Thermosetting Polymer x2,000 [reaction] (10 runs, 200/run)
        - Oxygen Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Atmospheric Gases x1,000  [raw]
        - Silicates x1,000  [raw]
    - Sense-Heuristic Neurolink Enhancer x7,680 [reaction] (384 runs, 20/run)
      - Hydrogen Fuel Block x1,920 [manufacturing] (48 runs, 40/run)
        - Robotics x48  [raw]
        - Enriched Uranium x192  [raw]
        - Mechanical Parts x192  [raw]
        - Coolant x432  [raw]
        - Strontium Clathrates x960  [raw]
        - Oxygen x1,056  [raw]
        - Heavy Water x8,160  [raw]
        - Liquid Ozone x16,800  [raw]
        - Hydrogen Isotopes x21,600  [raw]
      - Azure Mykoserocin x15,360  [raw]
      - Vermillion Mykoserocin x15,360  [raw]
      - AV-Composite Molecular Condenser x384  [raw]
    - Goal-Orienting Neurolink Stabilizer x192 [reaction] (20 runs, 10/run)
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
      - Vermillion Cytoserocin x200  [raw]
      - Azure Cytoserocin x200  [raw]
      - AV-Composite Molecular Condenser x20  [raw]
  - Capital Computer System x200 [manufacturing] (200 runs, 1/run)
    - Recursive Computing Module x200  [raw]
    - Reinforced Carbon Fiber x20,000 [reaction] (100 runs, 200/run)
      - Carbon Fiber x20,000 [reaction] (100 runs, 200/run)
        - Hydrogen Fuel Block x500 [manufacturing] (13 runs, 40/run)
          - Robotics x13  [raw]
          - Enriched Uranium x52  [raw]
          - Mechanical Parts x52  [raw]
          - Coolant x117  [raw]
          - Strontium Clathrates x260  [raw]
          - Oxygen x286  [raw]
          - Heavy Water x2,210  [raw]
          - Liquid Ozone x4,550  [raw]
          - Hydrogen Isotopes x5,850  [raw]
        - Hydrocarbons x10,000  [raw]
        - Evaporite Deposits x10,000  [raw]
      - Oxy-Organic Solvents x100 [reaction] (10 runs, 10/run)
        - Oxygen Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x20,000  [raw]
        - Atmospheric Gases x20,000  [raw]
      - Thermosetting Polymer x20,000 [reaction] (100 runs, 200/run)
        - Oxygen Fuel Block x500 [manufacturing] (13 runs, 40/run)
          - Robotics x13  [raw]
          - Enriched Uranium x52  [raw]
          - Mechanical Parts x52  [raw]
          - Coolant x117  [raw]
          - Strontium Clathrates x260  [raw]
          - Oxygen x286  [raw]
          - Heavy Water x2,210  [raw]
          - Liquid Ozone x4,550  [raw]
          - Oxygen Isotopes x5,850  [raw]
        - Atmospheric Gases x10,000  [raw]
        - Silicates x10,000  [raw]
    - Megacyte x57,000  [raw]
    - Zydrine x114,000  [raw]
    - Nocxium x225,000  [raw]
    - Isogen x2,250,000  [raw]
    - Tritanium x8,100,000  [raw]
    - Mexallon x8,100,000  [raw]
    - Pyerite x29,250,000  [raw]
  - Capital Construction Parts x200 [manufacturing] (200 runs, 1/run)
    - Reinforced Carbon Fiber x20,000 [reaction] (100 runs, 200/run)
      - Carbon Fiber x20,000 [reaction] (100 runs, 200/run)
        - Hydrogen Fuel Block x500 [manufacturing] (13 runs, 40/run)
          - Robotics x13  [raw]
          - Enriched Uranium x52  [raw]
          - Mechanical Parts x52  [raw]
          - Coolant x117  [raw]
          - Strontium Clathrates x260  [raw]
          - Oxygen x286  [raw]
          - Heavy Water x2,210  [raw]
          - Liquid Ozone x4,550  [raw]
          - Hydrogen Isotopes x5,850  [raw]
        - Hydrocarbons x10,000  [raw]
        - Evaporite Deposits x10,000  [raw]
      - Oxy-Organic Solvents x100 [reaction] (10 runs, 10/run)
        - Oxygen Fuel Block x50 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x20,000  [raw]
        - Atmospheric Gases x20,000  [raw]
      - Thermosetting Polymer x20,000 [reaction] (100 runs, 200/run)
        - Oxygen Fuel Block x500 [manufacturing] (13 runs, 40/run)
          - Robotics x13  [raw]
          - Enriched Uranium x52  [raw]
          - Mechanical Parts x52  [raw]
          - Coolant x117  [raw]
          - Strontium Clathrates x260  [raw]
          - Oxygen x286  [raw]
          - Heavy Water x2,210  [raw]
          - Liquid Ozone x4,550  [raw]
          - Oxygen Isotopes x5,850  [raw]
        - Atmospheric Gases x10,000  [raw]
        - Silicates x10,000  [raw]
    - Megacyte x42,000  [raw]
    - Zydrine x82,600  [raw]
    - Nocxium x150,000  [raw]
    - Isogen x1,800,000  [raw]
    - Tritanium x6,000,000  [raw]
    - Mexallon x6,000,000  [raw]
    - Pyerite x21,000,000  [raw]
  - Ladar-FTL Interlink Communicator x250 [manufacturing] (250 runs, 1/run)
    - Self-Harmonizing Power Core x250  [raw]
    - Wetware Mainframe x250  [raw]
    - Broadcast Node x500  [raw]
    - Fermionic Condensates x10,000 [reaction] (50 runs, 200/run)
      - Helium Fuel Block x250 [manufacturing] (7 runs, 40/run)
        - Robotics x7  [raw]
        - Enriched Uranium x28  [raw]
        - Mechanical Parts x28  [raw]
        - Coolant x63  [raw]
        - Strontium Clathrates x140  [raw]
        - Oxygen x154  [raw]
        - Heavy Water x1,190  [raw]
        - Liquid Ozone x2,450  [raw]
        - Helium Isotopes x3,150  [raw]
      - Caesarium Cadmide x5,000 [reaction] (25 runs, 200/run)
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
        - Cadmium x2,500  [raw]
        - Caesium x2,500  [raw]
      - Dysporite x5,000 [reaction] (25 runs, 200/run)
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
        - Mercury x2,500  [raw]
        - Dysprosium x2,500  [raw]
      - Fluxed Condensates x5,000 [reaction] (25 runs, 200/run)
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
        - Neodymium x2,500  [raw]
        - Thulium x2,500  [raw]
      - Prometium x5,000 [reaction] (25 runs, 200/run)
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
        - Cadmium x2,500  [raw]
        - Promethium x2,500  [raw]
    - Scandium Metallofullerene x32,500 [reaction] (204 runs, 160/run)
      - Helium Fuel Block x1,020 [manufacturing] (26 runs, 40/run)
        - Robotics x26  [raw]
        - Enriched Uranium x104  [raw]
        - Mechanical Parts x104  [raw]
        - Coolant x234  [raw]
        - Strontium Clathrates x520  [raw]
        - Oxygen x572  [raw]
        - Heavy Water x4,420  [raw]
        - Liquid Ozone x9,100  [raw]
        - Helium Isotopes x11,700  [raw]
      - Zydrine x5,100  [raw]
      - Fullerite-C72 x20,400  [raw]
      - Fullerite-C28 x20,400  [raw]
    - PPD Fullerene Fibers x47,500 [reaction] (190 runs, 250/run)
      - Hydrogen Fuel Block x950 [manufacturing] (24 runs, 40/run)
        - Robotics x24  [raw]
        - Enriched Uranium x96  [raw]
        - Mechanical Parts x96  [raw]
        - Coolant x216  [raw]
        - Strontium Clathrates x480  [raw]
        - Oxygen x528  [raw]
        - Heavy Water x4,080  [raw]
        - Liquid Ozone x8,400  [raw]
        - Hydrogen Isotopes x10,800  [raw]
      - Fullerite-C60 x19,000  [raw]
      - Fullerite-C50 x57,000  [raw]
      - Pyerite x152,000  [raw]
    - Methanofullerene x47,500 [reaction] (297 runs, 160/run)
      - Hydrogen Fuel Block x1,485 [manufacturing] (38 runs, 40/run)
        - Robotics x38  [raw]
        - Enriched Uranium x152  [raw]
        - Mechanical Parts x152  [raw]
        - Coolant x342  [raw]
        - Strontium Clathrates x760  [raw]
        - Oxygen x836  [raw]
        - Heavy Water x6,460  [raw]
        - Liquid Ozone x13,300  [raw]
        - Hydrogen Isotopes x17,100  [raw]
      - Fullerite-C70 x29,700  [raw]
      - Fullerite-C72 x29,700  [raw]
      - Isogen x89,100  [raw]
    - Lanthanum Metallofullerene x47,500 [reaction] (396 runs, 120/run)
      - Oxygen Fuel Block x1,980 [manufacturing] (50 runs, 40/run)
        - Robotics x50  [raw]
        - Enriched Uranium x200  [raw]
        - Mechanical Parts x200  [raw]
        - Coolant x450  [raw]
        - Strontium Clathrates x1,000  [raw]
        - Oxygen x1,100  [raw]
        - Heavy Water x8,500  [raw]
        - Liquid Ozone x17,500  [raw]
        - Oxygen Isotopes x22,500  [raw]
      - Fullerite-C70 x39,600  [raw]
      - Fullerite-C84 x39,600  [raw]
      - Nocxium x79,200  [raw]
    - C3-FTM Acid x65,000 [reaction] (650 runs, 100/run)
      - Helium Fuel Block x3,250 [manufacturing] (82 runs, 40/run)
        - Robotics x82  [raw]
        - Enriched Uranium x328  [raw]
        - Mechanical Parts x328  [raw]
        - Coolant x738  [raw]
        - Strontium Clathrates x1,640  [raw]
        - Oxygen x1,804  [raw]
        - Heavy Water x13,940  [raw]
        - Liquid Ozone x28,700  [raw]
        - Helium Isotopes x36,900  [raw]
      - Megacyte x52,000  [raw]
      - Fullerite-C84 x65,000  [raw]
      - Fullerite-C540 x65,000  [raw]
    - Carbon-86 Epoxy Resin x95,000 [reaction] (594 runs, 160/run)
      - Nitrogen Fuel Block x2,970 [manufacturing] (75 runs, 40/run)
        - Robotics x75  [raw]
        - Enriched Uranium x300  [raw]
        - Mechanical Parts x300  [raw]
        - Coolant x675  [raw]
        - Strontium Clathrates x1,500  [raw]
        - Oxygen x1,650  [raw]
        - Heavy Water x12,750  [raw]
        - Liquid Ozone x26,250  [raw]
        - Nitrogen Isotopes x33,750  [raw]
      - Zydrine x17,820  [raw]
      - Fullerite-C32 x59,400  [raw]
      - Fullerite-C320 x59,400  [raw]
    - Fullerene Intercalated Graphite x97,500 [reaction] (813 runs, 120/run)
      - Hydrogen Fuel Block x4,065 [manufacturing] (102 runs, 40/run)
        - Robotics x102  [raw]
        - Enriched Uranium x408  [raw]
        - Mechanical Parts x408  [raw]
        - Coolant x918  [raw]
        - Strontium Clathrates x2,040  [raw]
        - Oxygen x2,244  [raw]
        - Heavy Water x17,340  [raw]
        - Liquid Ozone x35,700  [raw]
        - Hydrogen Isotopes x45,900  [raw]
      - Fullerite-C60 x81,300  [raw]
      - Fullerite-C70 x81,300  [raw]
      - Mexallon x487,800  [raw]
    - Graphene Nanoribbons x140,000 [reaction] (1,167 runs, 120/run)
      - Nitrogen Fuel Block x5,835 [manufacturing] (146 runs, 40/run)
        - Robotics x146  [raw]
        - Enriched Uranium x584  [raw]
        - Mechanical Parts x584  [raw]
        - Coolant x1,314  [raw]
        - Strontium Clathrates x2,920  [raw]
        - Oxygen x3,212  [raw]
        - Heavy Water x24,820  [raw]
        - Liquid Ozone x51,100  [raw]
        - Nitrogen Isotopes x65,700  [raw]
      - Fullerite-C28 x116,700  [raw]
      - Fullerite-C32 x116,700  [raw]
      - Nocxium x466,800  [raw]
    - Plasmonic Metamaterials x140,000 [reaction] (467 runs, 300/run)
      - Hydrogen Fuel Block x2,335 [manufacturing] (59 runs, 40/run)
        - Robotics x59  [raw]
        - Enriched Uranium x236  [raw]
        - Mechanical Parts x236  [raw]
        - Coolant x531  [raw]
        - Strontium Clathrates x1,180  [raw]
        - Oxygen x1,298  [raw]
        - Heavy Water x10,030  [raw]
        - Liquid Ozone x20,650  [raw]
        - Hydrogen Isotopes x26,550  [raw]
      - Fernite Alloy x46,700 [reaction] (234 runs, 200/run)
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
        - Scandium x23,400  [raw]
        - Vanadium x23,400  [raw]
      - Neo Mercurite x46,700 [reaction] (234 runs, 200/run)
        - Helium Fuel Block x1,170 [manufacturing] (30 runs, 40/run)
          - Robotics x30  [raw]
          - Enriched Uranium x120  [raw]
          - Mechanical Parts x120  [raw]
          - Coolant x270  [raw]
          - Strontium Clathrates x600  [raw]
          - Oxygen x660  [raw]
          - Heavy Water x5,100  [raw]
          - Liquid Ozone x10,500  [raw]
          - Helium Isotopes x13,500  [raw]
        - Mercury x23,400  [raw]
        - Neodymium x23,400  [raw]
    - Fulleroferrocene x165,000 [reaction] (165 runs, 1000/run)
      - Oxygen Fuel Block x825 [manufacturing] (21 runs, 40/run)
        - Robotics x21  [raw]
        - Enriched Uranium x84  [raw]
        - Mechanical Parts x84  [raw]
        - Coolant x189  [raw]
        - Strontium Clathrates x420  [raw]
        - Oxygen x462  [raw]
        - Heavy Water x3,570  [raw]
        - Liquid Ozone x7,350  [raw]
        - Oxygen Isotopes x9,450  [raw]
      - Fullerite-C60 x16,500  [raw]
      - Fullerite-C50 x33,000  [raw]
      - Tritanium x165,000  [raw]
  - Capital Armor Plates x300 [manufacturing] (300 runs, 1/run)
    - Organic Mortar Applicators x1,500  [raw]
    - Reinforced Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
      - Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
        - Hydrogen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Hydrogen Isotopes x8,550  [raw]
        - Hydrocarbons x15,000  [raw]
        - Evaporite Deposits x15,000  [raw]
      - Oxy-Organic Solvents x150 [reaction] (15 runs, 10/run)
        - Oxygen Fuel Block x75 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x30,000  [raw]
        - Atmospheric Gases x30,000  [raw]
      - Thermosetting Polymer x30,000 [reaction] (150 runs, 200/run)
        - Oxygen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Oxygen Isotopes x8,550  [raw]
        - Atmospheric Gases x15,000  [raw]
        - Silicates x15,000  [raw]
    - Megacyte x92,400  [raw]
    - Zydrine x184,500  [raw]
    - Nocxium x360,000  [raw]
    - Isogen x3,600,000  [raw]
    - Tritanium x13,500,000  [raw]
    - Mexallon x13,500,000  [raw]
    - Pyerite x47,250,000  [raw]
  - Capital Capacitor Battery x300 [manufacturing] (300 runs, 1/run)
    - Self-Harmonizing Power Core x300  [raw]
    - Reinforced Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
      - Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
        - Hydrogen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Hydrogen Isotopes x8,550  [raw]
        - Hydrocarbons x15,000  [raw]
        - Evaporite Deposits x15,000  [raw]
      - Oxy-Organic Solvents x150 [reaction] (15 runs, 10/run)
        - Oxygen Fuel Block x75 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x30,000  [raw]
        - Atmospheric Gases x30,000  [raw]
      - Thermosetting Polymer x30,000 [reaction] (150 runs, 200/run)
        - Oxygen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Oxygen Isotopes x8,550  [raw]
        - Atmospheric Gases x15,000  [raw]
        - Silicates x15,000  [raw]
    - Megacyte x83,400  [raw]
    - Zydrine x164,400  [raw]
    - Nocxium x337,500  [raw]
    - Isogen x3,375,000  [raw]
    - Tritanium x11,700,000  [raw]
    - Mexallon x11,700,000  [raw]
    - Pyerite x42,750,000  [raw]
  - Capital Jump Drive x300 [manufacturing] (300 runs, 1/run)
    - Wetware Mainframe x300  [raw]
    - Reinforced Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
      - Carbon Fiber x30,000 [reaction] (150 runs, 200/run)
        - Hydrogen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Hydrogen Isotopes x8,550  [raw]
        - Hydrocarbons x15,000  [raw]
        - Evaporite Deposits x15,000  [raw]
      - Oxy-Organic Solvents x150 [reaction] (15 runs, 10/run)
        - Oxygen Fuel Block x75 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Hydrocarbons x30,000  [raw]
        - Atmospheric Gases x30,000  [raw]
      - Thermosetting Polymer x30,000 [reaction] (150 runs, 200/run)
        - Oxygen Fuel Block x750 [manufacturing] (19 runs, 40/run)
          - Robotics x19  [raw]
          - Enriched Uranium x76  [raw]
          - Mechanical Parts x76  [raw]
          - Coolant x171  [raw]
          - Strontium Clathrates x380  [raw]
          - Oxygen x418  [raw]
          - Heavy Water x3,230  [raw]
          - Liquid Ozone x6,650  [raw]
          - Oxygen Isotopes x8,550  [raw]
        - Atmospheric Gases x15,000  [raw]
        - Silicates x15,000  [raw]
    - Megacyte x126,000  [raw]
    - Zydrine x270,000  [raw]
    - Nocxium x506,400  [raw]
    - Isogen x5,062,500  [raw]
    - Tritanium x18,000,000  [raw]
    - Mexallon x18,000,000  [raw]
    - Pyerite x64,800,000  [raw]
  - Capital Turret Hardpoint x400 [manufacturing] (400 runs, 1/run)
    - Wetware Mainframe x400  [raw]
    - Reinforced Carbon Fiber x40,000 [reaction] (200 runs, 200/run)
      - Carbon Fiber x40,000 [reaction] (200 runs, 200/run)
        - Hydrogen Fuel Block x1,000 [manufacturing] (25 runs, 40/run)
          - Robotics x25  [raw]
          - Enriched Uranium x100  [raw]
          - Mechanical Parts x100  [raw]
          - Coolant x225  [raw]
          - Strontium Clathrates x500  [raw]
          - Oxygen x550  [raw]
          - Heavy Water x4,250  [raw]
          - Liquid Ozone x8,750  [raw]
          - Hydrogen Isotopes x11,250  [raw]
        - Hydrocarbons x20,000  [raw]
        - Evaporite Deposits x20,000  [raw]
      - Oxy-Organic Solvents x200 [reaction] (20 runs, 10/run)
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
        - Hydrocarbons x40,000  [raw]
        - Atmospheric Gases x40,000  [raw]
      - Thermosetting Polymer x40,000 [reaction] (200 runs, 200/run)
        - Oxygen Fuel Block x1,000 [manufacturing] (25 runs, 40/run)
          - Robotics x25  [raw]
          - Enriched Uranium x100  [raw]
          - Mechanical Parts x100  [raw]
          - Coolant x225  [raw]
          - Strontium Clathrates x500  [raw]
          - Oxygen x550  [raw]
          - Heavy Water x4,250  [raw]
          - Liquid Ozone x8,750  [raw]
          - Oxygen Isotopes x11,250  [raw]
        - Atmospheric Gases x20,000  [raw]
        - Silicates x20,000  [raw]
    - Megacyte x75,200  [raw]
    - Zydrine x156,000  [raw]
    - Nocxium x300,000  [raw]
    - Isogen x3,000,000  [raw]
    - Tritanium x11,100,000  [raw]
    - Mexallon x11,400,000  [raw]
    - Pyerite x40,500,000  [raw]
  - Capital Power Generator x400 [manufacturing] (400 runs, 1/run)
    - Self-Harmonizing Power Core x400  [raw]
    - Reinforced Carbon Fiber x40,000 [reaction] (200 runs, 200/run)
      - Carbon Fiber x40,000 [reaction] (200 runs, 200/run)
        - Hydrogen Fuel Block x1,000 [manufacturing] (25 runs, 40/run)
          - Robotics x25  [raw]
          - Enriched Uranium x100  [raw]
          - Mechanical Parts x100  [raw]
          - Coolant x225  [raw]
          - Strontium Clathrates x500  [raw]
          - Oxygen x550  [raw]
          - Heavy Water x4,250  [raw]
          - Liquid Ozone x8,750  [raw]
          - Hydrogen Isotopes x11,250  [raw]
        - Hydrocarbons x20,000  [raw]
        - Evaporite Deposits x20,000  [raw]
      - Oxy-Organic Solvents x200 [reaction] (20 runs, 10/run)
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
        - Hydrocarbons x40,000  [raw]
        - Atmospheric Gases x40,000  [raw]
      - Thermosetting Polymer x40,000 [reaction] (200 runs, 200/run)
        - Oxygen Fuel Block x1,000 [manufacturing] (25 runs, 40/run)
          - Robotics x25  [raw]
          - Enriched Uranium x100  [raw]
          - Mechanical Parts x100  [raw]
          - Coolant x225  [raw]
          - Strontium Clathrates x500  [raw]
          - Oxygen x550  [raw]
          - Heavy Water x4,250  [raw]
          - Liquid Ozone x8,750  [raw]
          - Oxygen Isotopes x11,250  [raw]
        - Atmospheric Gases x20,000  [raw]
        - Silicates x20,000  [raw]
    - Megacyte x132,000  [raw]
    - Zydrine x264,000  [raw]
    - Nocxium x540,000  [raw]
    - Isogen x5,400,000  [raw]
    - Tritanium x18,900,000  [raw]
    - Mexallon x18,900,000  [raw]
    - Pyerite x67,500,000  [raw]
  - Capital Jump Bridge Array x500 [manufacturing] (500 runs, 1/run)
    - Wetware Mainframe x500  [raw]
    - Broadcast Node x1,000  [raw]
    - Reinforced Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
      - Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
        - Hydrogen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Hydrogen Isotopes x14,400  [raw]
        - Hydrocarbons x25,000  [raw]
        - Evaporite Deposits x25,000  [raw]
      - Oxy-Organic Solvents x250 [reaction] (25 runs, 10/run)
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
        - Hydrocarbons x50,000  [raw]
        - Atmospheric Gases x50,000  [raw]
      - Thermosetting Polymer x50,000 [reaction] (250 runs, 200/run)
        - Oxygen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Oxygen Isotopes x14,400  [raw]
        - Atmospheric Gases x25,000  [raw]
        - Silicates x25,000  [raw]
    - Megacyte x562,500  [raw]
    - Zydrine x1,125,000  [raw]
    - Nocxium x2,250,000  [raw]
    - Isogen x18,562,500  [raw]
    - Mexallon x67,500,000  [raw]
    - Tritanium x75,000,000  [raw]
    - Pyerite x247,500,000  [raw]
  - Capital Clone Vat Bay x500 [manufacturing] (500 runs, 1/run)
    - Integrity Response Drones x1,000  [raw]
    - Sterile Conduits x1,000  [raw]
    - Reinforced Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
      - Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
        - Hydrogen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Hydrogen Isotopes x14,400  [raw]
        - Hydrocarbons x25,000  [raw]
        - Evaporite Deposits x25,000  [raw]
      - Oxy-Organic Solvents x250 [reaction] (25 runs, 10/run)
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
        - Hydrocarbons x50,000  [raw]
        - Atmospheric Gases x50,000  [raw]
      - Thermosetting Polymer x50,000 [reaction] (250 runs, 200/run)
        - Oxygen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Oxygen Isotopes x14,400  [raw]
        - Atmospheric Gases x25,000  [raw]
        - Silicates x25,000  [raw]
    - Megacyte x244,000  [raw]
    - Zydrine x478,000  [raw]
    - Nocxium x937,500  [raw]
    - Isogen x8,437,500  [raw]
    - Mexallon x30,375,000  [raw]
    - Tritanium x33,750,000  [raw]
    - Pyerite x121,875,000  [raw]
  - Capital Doomsday Weapon Mount x500 [manufacturing] (500 runs, 1/run)
    - Wetware Mainframe x500  [raw]
    - Nano-Factory x2,500  [raw]
    - Reinforced Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
      - Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
        - Hydrogen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Hydrogen Isotopes x14,400  [raw]
        - Hydrocarbons x25,000  [raw]
        - Evaporite Deposits x25,000  [raw]
      - Oxy-Organic Solvents x250 [reaction] (25 runs, 10/run)
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
        - Hydrocarbons x50,000  [raw]
        - Atmospheric Gases x50,000  [raw]
      - Thermosetting Polymer x50,000 [reaction] (250 runs, 200/run)
        - Oxygen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Oxygen Isotopes x14,400  [raw]
        - Atmospheric Gases x25,000  [raw]
        - Silicates x25,000  [raw]
    - Megacyte x375,000  [raw]
    - Zydrine x750,000  [raw]
    - Nocxium x1,500,000  [raw]
    - Isogen x13,500,000  [raw]
    - Mexallon x45,562,500  [raw]
    - Tritanium x50,625,000  [raw]
    - Pyerite x187,500,000  [raw]
  - Capital Ship Maintenance Bay x500 [manufacturing] (500 runs, 1/run)
    - Integrity Response Drones x500  [raw]
    - Reinforced Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
      - Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
        - Hydrogen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Hydrogen Isotopes x14,400  [raw]
        - Hydrocarbons x25,000  [raw]
        - Evaporite Deposits x25,000  [raw]
      - Oxy-Organic Solvents x250 [reaction] (25 runs, 10/run)
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
        - Hydrocarbons x50,000  [raw]
        - Atmospheric Gases x50,000  [raw]
      - Thermosetting Polymer x50,000 [reaction] (250 runs, 200/run)
        - Oxygen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Oxygen Isotopes x14,400  [raw]
        - Atmospheric Gases x25,000  [raw]
        - Silicates x25,000  [raw]
    - Megacyte x187,500  [raw]
    - Zydrine x375,000  [raw]
    - Nocxium x750,000  [raw]
    - Isogen x7,500,000  [raw]
    - Tritanium x27,000,000  [raw]
    - Mexallon x27,000,000  [raw]
    - Pyerite x96,000,000  [raw]
  - Capital Corporate Hangar Bay x500 [manufacturing] (500 runs, 1/run)
    - Reinforced Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
      - Carbon Fiber x50,000 [reaction] (250 runs, 200/run)
        - Hydrogen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Hydrogen Isotopes x14,400  [raw]
        - Hydrocarbons x25,000  [raw]
        - Evaporite Deposits x25,000  [raw]
      - Oxy-Organic Solvents x250 [reaction] (25 runs, 10/run)
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
        - Hydrocarbons x50,000  [raw]
        - Atmospheric Gases x50,000  [raw]
      - Thermosetting Polymer x50,000 [reaction] (250 runs, 200/run)
        - Oxygen Fuel Block x1,250 [manufacturing] (32 runs, 40/run)
          - Robotics x32  [raw]
          - Enriched Uranium x128  [raw]
          - Mechanical Parts x128  [raw]
          - Coolant x288  [raw]
          - Strontium Clathrates x640  [raw]
          - Oxygen x704  [raw]
          - Heavy Water x5,440  [raw]
          - Liquid Ozone x11,200  [raw]
          - Oxygen Isotopes x14,400  [raw]
        - Atmospheric Gases x25,000  [raw]
        - Silicates x25,000  [raw]
    - Megacyte x199,000  [raw]
    - Zydrine x394,000  [raw]
    - Nocxium x825,000  [raw]
    - Isogen x8,250,000  [raw]
    - Tritanium x28,125,000  [raw]
    - Mexallon x28,125,000  [raw]
    - Pyerite x101,250,000  [raw]
  - Life Support Backup Unit x1,600 [manufacturing] (534 runs, 3/run)
    - Test Cultures x4,272  [raw]
    - Viral Agent x4,272  [raw]
    - Reinforced Carbon Fiber x5,340 [reaction] (27 runs, 200/run)
      - Carbon Fiber x5,400 [reaction] (27 runs, 200/run)
        - Hydrogen Fuel Block x135 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Hydrogen Isotopes x1,800  [raw]
        - Hydrocarbons x2,700  [raw]
        - Evaporite Deposits x2,700  [raw]
      - Oxy-Organic Solvents x27 [reaction] (3 runs, 10/run)
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
      - Thermosetting Polymer x5,400 [reaction] (27 runs, 200/run)
        - Oxygen Fuel Block x135 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Oxygen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,700  [raw]
        - Silicates x2,700  [raw]
  - Auto-Integrity Preservation Seal x3,200 [manufacturing] (1,067 runs, 3/run)
    - Supertensile Plastics x4,268  [raw]
    - Nanites x4,268  [raw]
    - Reinforced Carbon Fiber x10,670 [reaction] (54 runs, 200/run)
      - Carbon Fiber x10,800 [reaction] (54 runs, 200/run)
        - Hydrogen Fuel Block x270 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Hydrogen Isotopes x3,150  [raw]
        - Hydrocarbons x5,400  [raw]
        - Evaporite Deposits x5,400  [raw]
      - Oxy-Organic Solvents x54 [reaction] (6 runs, 10/run)
        - Oxygen Fuel Block x30 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Oxygen Isotopes x450  [raw]
        - Hydrocarbons x12,000  [raw]
        - Atmospheric Gases x12,000  [raw]
      - Thermosetting Polymer x10,800 [reaction] (54 runs, 200/run)
        - Oxygen Fuel Block x270 [manufacturing] (7 runs, 40/run)
          - Robotics x7  [raw]
          - Enriched Uranium x28  [raw]
          - Mechanical Parts x28  [raw]
          - Coolant x63  [raw]
          - Strontium Clathrates x140  [raw]
          - Oxygen x154  [raw]
          - Heavy Water x1,190  [raw]
          - Liquid Ozone x2,450  [raw]
          - Oxygen Isotopes x3,150  [raw]
        - Atmospheric Gases x5,400  [raw]
        - Silicates x5,400  [raw]
```

## Aggregated phases (shared intermediates merged)

### Phase 6

| Type | Required | Activity / runs |
|---|---:|---|
| Ragnarok | 1 | manufacturing, 1 runs |

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Capital Propulsion Engine | 80 | manufacturing, 80 runs |
| Capital Turret Hardpoint | 400 | manufacturing, 400 runs |
| Capital Sensor Cluster | 100 | manufacturing, 100 runs |
| Capital Armor Plates | 300 | manufacturing, 300 runs |
| Capital Capacitor Battery | 300 | manufacturing, 300 runs |
| Capital Power Generator | 400 | manufacturing, 400 runs |
| Capital Shield Emitter | 150 | manufacturing, 150 runs |
| Capital Jump Drive | 300 | manufacturing, 300 runs |
| Capital Computer System | 200 | manufacturing, 200 runs |
| Capital Construction Parts | 200 | manufacturing, 200 runs |
| Capital Jump Bridge Array | 500 | manufacturing, 500 runs |
| Capital Clone Vat Bay | 500 | manufacturing, 500 runs |
| Capital Doomsday Weapon Mount | 500 | manufacturing, 500 runs |
| Capital Ship Maintenance Bay | 500 | manufacturing, 500 runs |
| Capital Corporate Hangar Bay | 500 | manufacturing, 500 runs |
| G-O Trigger Neurolink Conduit | 192 | manufacturing, 192 runs |
| Ladar-FTL Interlink Communicator | 250 | manufacturing, 250 runs |
| Auto-Integrity Preservation Seal | 3,200 | manufacturing, 1,067 runs |
| Life Support Backup Unit | 1,600 | manufacturing, 534 runs |
| Capital Core Temperature Regulator | 25 | manufacturing, 25 runs |
| Enhanced Neurolink Protection Cell | 1 | manufacturing, 1 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Counter-Subversion Sensor Array | 10 | raw (terminator) |
| Nanoscale Filter Plate | 10 | raw (terminator) |
| Enhanced Electro-Neural Signaller | 10 | raw (terminator) |
| Nano Regulation Gate | 20 | raw (terminator) |
| Synthetic Synapses | 3,000 | raw (terminator) |
| Miniature Electronics | 15,000 | raw (terminator) |
| Integrity Response Drones | 2,000 | raw (terminator) |
| Self-Harmonizing Power Core | 1,530 | raw (terminator) |
| Megacyte | 2,273,500 | raw (terminator) |
| Zydrine | 4,552,350 | raw (terminator) |
| Nocxium | 9,063,900 | raw (terminator) |
| Isogen | 84,562,500 | raw (terminator) |
| Tritanium | 315,840,000 | raw (terminator) |
| Mexallon | 300,202,500 | raw (terminator) |
| Pyerite | 1,117,125,000 | raw (terminator) |
| Broadcast Node | 1,600 | raw (terminator) |
| Recursive Computing Module | 350 | raw (terminator) |
| Wetware Mainframe | 1,950 | raw (terminator) |
| Organic Mortar Applicators | 1,500 | raw (terminator) |
| Sterile Conduits | 1,000 | raw (terminator) |
| Nano-Factory | 2,500 | raw (terminator) |
| Test Cultures | 4,272 | raw (terminator) |
| Viral Agent | 4,272 | raw (terminator) |
| Supertensile Plastics | 4,268 | raw (terminator) |
| Nanites | 4,268 | raw (terminator) |
| Fermionic Condensates | 10,000 | reaction, 50 runs |
| Fulleroferrocene | 165,000 | reaction, 165 runs |
| PPD Fullerene Fibers | 47,500 | reaction, 190 runs |
| Fullerene Intercalated Graphite | 97,500 | reaction, 813 runs |
| Methanofullerene | 47,500 | reaction, 297 runs |
| Lanthanum Metallofullerene | 47,500 | reaction, 396 runs |
| Scandium Metallofullerene | 32,500 | reaction, 204 runs |
| Graphene Nanoribbons | 140,000 | reaction, 1,167 runs |
| Carbon-86 Epoxy Resin | 95,000 | reaction, 594 runs |
| C3-FTM Acid | 65,000 | reaction, 650 runs |
| Plasmonic Metamaterials | 140,000 | reaction, 467 runs |
| Pressurized Oxidizers | 1,920 | reaction, 10 runs |
| Reinforced Carbon Fiber | 510,930 | reaction, 2,555 runs |
| Meta-Operant Neurolink Enhancer | 150 | reaction, 8 runs |
| Sense-Heuristic Neurolink Enhancer | 7,680 | reaction, 384 runs |
| Goal-Orienting Neurolink Stabilizer | 192 | reaction, 20 runs |
| Core Temperature Regulator | 875 | manufacturing, 875 runs |
| Genetic Safeguard Filter | 75 | manufacturing, 75 runs |
| Neurolink Enhancer Reservoir | 10 | manufacturing, 10 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Meta-Molecular Combiner | 8 | raw (terminator) |
| Chiral Structures | 87,500 | raw (terminator) |
| Water | 87,500 | raw (terminator) |
| Azure Mykoserocin | 15,360 | raw (terminator) |
| Vermillion Mykoserocin | 15,360 | raw (terminator) |
| AV-Composite Molecular Condenser | 404 | raw (terminator) |
| Vermillion Cytoserocin | 200 | raw (terminator) |
| Azure Cytoserocin | 200 | raw (terminator) |
| Zydrine | 22,920 | raw (terminator) |
| Fullerite-C72 | 50,100 | raw (terminator) |
| Fullerite-C28 | 137,100 | raw (terminator) |
| Fullerite-C60 | 116,800 | raw (terminator) |
| Fullerite-C50 | 90,000 | raw (terminator) |
| Pyerite | 152,000 | raw (terminator) |
| Fullerite-C70 | 150,600 | raw (terminator) |
| Isogen | 89,100 | raw (terminator) |
| Fullerite-C84 | 104,600 | raw (terminator) |
| Nocxium | 546,000 | raw (terminator) |
| Megacyte | 52,000 | raw (terminator) |
| Fullerite-C540 | 65,000 | raw (terminator) |
| Fullerite-C32 | 176,100 | raw (terminator) |
| Fullerite-C320 | 59,400 | raw (terminator) |
| Mexallon | 487,800 | raw (terminator) |
| Tritanium | 165,000 | raw (terminator) |
| Nitrogen Fuel Block | 8,805 | manufacturing, 221 runs |
| Hydrogen Fuel Block | 10,895 | manufacturing, 273 runs |
| Helium Fuel Block | 4,520 | manufacturing, 113 runs |
| Oxygen Fuel Block | 2,805 | manufacturing, 71 runs |
| Fernite Alloy | 46,700 | reaction, 234 runs |
| Carbon Polymers | 2,000 | reaction, 10 runs |
| Sulfuric Acid | 2,000 | reaction, 10 runs |
| Caesarium Cadmide | 5,000 | reaction, 25 runs |
| Neo Mercurite | 46,700 | reaction, 234 runs |
| Dysporite | 5,000 | reaction, 25 runs |
| Fluxed Condensates | 5,000 | reaction, 25 runs |
| Prometium | 5,000 | reaction, 25 runs |
| Carbon Fiber | 511,000 | reaction, 2,555 runs |
| Oxy-Organic Solvents | 2,565 | reaction, 257 runs |
| Thermosetting Polymer | 511,000 | reaction, 2,555 runs |
| Pressurized Oxidizers | 437,500 | reaction, 2,188 runs |
| Reinforced Carbon Fiber | 442,500 | reaction, 2,213 runs |
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
| Hermetic Membranes | 1,000 | raw (terminator) |
| Gel-Matrix Biopaste | 3,000 | raw (terminator) |
| Morphite | 15,000 | raw (terminator) |
| Biocells | 1,875 | raw (terminator) |
| Nanites | 1,875 | raw (terminator) |
| Test Cultures | 1,875 | raw (terminator) |
| Robotics | 678 | raw (terminator) |
| Enriched Uranium | 2,712 | raw (terminator) |
| Mechanical Parts | 2,712 | raw (terminator) |
| Coolant | 6,102 | raw (terminator) |
| Strontium Clathrates | 13,560 | raw (terminator) |
| Oxygen | 14,916 | raw (terminator) |
| Heavy Water | 115,260 | raw (terminator) |
| Liquid Ozone | 237,300 | raw (terminator) |
| Hydrogen Isotopes | 122,850 | raw (terminator) |
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
| Hydrocarbons | 770,500 | raw (terminator) |
| Evaporite Deposits | 256,500 | raw (terminator) |
| Atmospheric Gases | 770,500 | raw (terminator) |
| Silicates | 256,500 | raw (terminator) |
| Helium Isotopes | 50,850 | raw (terminator) |
| Cadmium | 5,000 | raw (terminator) |
| Caesium | 2,500 | raw (terminator) |
| Mercury | 25,900 | raw (terminator) |
| Dysprosium | 2,500 | raw (terminator) |
| Neodymium | 25,900 | raw (terminator) |
| Thulium | 2,500 | raw (terminator) |
| Promethium | 2,500 | raw (terminator) |
| Oxygen Isotopes | 31,950 | raw (terminator) |
| Nitrogen Isotopes | 99,450 | raw (terminator) |
| Scandium | 23,400 | raw (terminator) |
| Vanadium | 23,400 | raw (terminator) |
| Nitrogen Fuel Block | 210 | manufacturing, 6 runs |
| Hydrogen Fuel Block | 14,105 | manufacturing, 353 runs |
| Helium Fuel Block | 1,505 | manufacturing, 38 runs |
| Oxygen Fuel Block | 14,595 | manufacturing, 365 runs |
| Carbon Polymers | 437,600 | reaction, 2,188 runs |
| Sulfuric Acid | 437,600 | reaction, 2,188 runs |
| Carbon Fiber | 442,600 | reaction, 2,213 runs |
| Oxy-Organic Solvents | 4,401 | reaction, 441 runs |
| Thermosetting Polymer | 442,600 | reaction, 2,213 runs |
| Isotropic Neofullerene Alpha-3 | 1,875 | reaction, 94 runs |
| Isotropic Neofullerene Beta-6 | 1,875 | reaction, 94 runs |
| Isotropic Neofullerene Gamma-9 | 1,875 | reaction, 94 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrocarbons | 1,322,100 | raw (terminator) |
| Evaporite Deposits | 440,100 | raw (terminator) |
| Atmospheric Gases | 1,322,100 | raw (terminator) |
| Silicates | 440,100 | raw (terminator) |
| Tritanium | 2,820,000 | raw (terminator) |
| Fullerite-C60 | 47,000 | raw (terminator) |
| Fullerite-C84 | 47,000 | raw (terminator) |
| Isotropic Deposition Guide | 282 | raw (terminator) |
| Fullerite-C70 | 47,000 | raw (terminator) |
| Fullerite-C28 | 47,000 | raw (terminator) |
| Fullerite-C50 | 47,000 | raw (terminator) |
| Fullerite-C72 | 47,000 | raw (terminator) |
| Robotics | 762 | raw (terminator) |
| Enriched Uranium | 3,048 | raw (terminator) |
| Mechanical Parts | 3,048 | raw (terminator) |
| Coolant | 6,858 | raw (terminator) |
| Strontium Clathrates | 15,240 | raw (terminator) |
| Oxygen | 16,764 | raw (terminator) |
| Heavy Water | 129,540 | raw (terminator) |
| Liquid Ozone | 266,700 | raw (terminator) |
| Helium Isotopes | 17,100 | raw (terminator) |
| Nitrogen Isotopes | 2,700 | raw (terminator) |
| Oxygen Isotopes | 164,250 | raw (terminator) |
| Hydrogen Isotopes | 158,850 | raw (terminator) |
| Nitrogen Fuel Block | 11,410 | manufacturing, 286 runs |
| Hydrogen Fuel Block | 11,535 | manufacturing, 289 runs |
| Helium Fuel Block | 11,410 | manufacturing, 286 runs |
| Oxygen Fuel Block | 13,270 | manufacturing, 332 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 1,193 | raw (terminator) |
| Enriched Uranium | 4,772 | raw (terminator) |
| Mechanical Parts | 4,772 | raw (terminator) |
| Coolant | 10,737 | raw (terminator) |
| Strontium Clathrates | 23,860 | raw (terminator) |
| Oxygen | 26,246 | raw (terminator) |
| Heavy Water | 202,810 | raw (terminator) |
| Liquid Ozone | 417,550 | raw (terminator) |
| Hydrogen Isotopes | 130,050 | raw (terminator) |
| Oxygen Isotopes | 149,400 | raw (terminator) |
| Helium Isotopes | 128,700 | raw (terminator) |
| Nitrogen Isotopes | 128,700 | raw (terminator) |

## Raw-material acquisition table (Ragnarok ×1)

| Mineral | Required |
|---|---:|
| Pyerite | 1,117,277,000 |
| Tritanium | 318,825,000 |
| Mexallon | 300,690,300 |
| Isogen | 84,651,600 |
| Nocxium | 9,609,900 |
| Zydrine | 4,575,270 |
| Megacyte | 2,325,500 |

| Moon material | Required |
|---|---:|
| Hydrocarbons | 2,092,600 |
| Atmospheric Gases | 2,092,600 |
| Silicates | 696,600 |
| Evaporite Deposits | 696,600 |
| Mercury | 25,900 |
| Neodymium | 25,900 |
| Vanadium | 23,400 |
| Scandium | 23,400 |
| Morphite | 15,000 |
| Cadmium | 5,000 |
| Caesium | 2,500 |
| Dysprosium | 2,500 |
| Promethium | 2,500 |
| Thulium | 2,500 |

| PI commodity | Required |
|---|---:|
| Chiral Structures | 87,500 |
| Water | 87,500 |
| Coolant | 23,697 |
| Miniature Electronics | 15,000 |
| Enriched Uranium | 10,532 |
| Mechanical Parts | 10,532 |
| Test Cultures | 6,147 |
| Nanites | 6,143 |
| Viral Agent | 4,272 |
| Supertensile Plastics | 4,268 |
| Synthetic Synapses | 3,000 |
| Gel-Matrix Biopaste | 3,000 |
| Robotics | 2,633 |
| Nano-Factory | 2,500 |
| Integrity Response Drones | 2,000 |
| Wetware Mainframe | 1,950 |
| Biocells | 1,875 |
| Broadcast Node | 1,600 |
| Self-Harmonizing Power Core | 1,530 |
| Organic Mortar Applicators | 1,500 |
| Hermetic Membranes | 1,000 |
| Sterile Conduits | 1,000 |
| Recursive Computing Module | 350 |

| Ice product | Required |
|---|---:|
| Liquid Ozone | 921,550 |
| Heavy Water | 447,610 |
| Hydrogen Isotopes | 411,750 |
| Oxygen Isotopes | 345,600 |
| Nitrogen Isotopes | 230,850 |
| Helium Isotopes | 196,650 |
| Oxygen | 57,926 |
| Strontium Clathrates | 52,660 |

| Gas (harvestable clouds) | Required |
|---|---:|
| Fullerite-C70 | 197,600 |
| Fullerite-C28 | 184,100 |
| Fullerite-C32 | 176,100 |
| Fullerite-C60 | 163,800 |
| Fullerite-C84 | 151,600 |
| Fullerite-C50 | 137,000 |
| Fullerite-C72 | 97,100 |
| Fullerite-C540 | 65,000 |
| Fullerite-C320 | 59,400 |
| Azure Mykoserocin | 16,640 |
| Vermillion Mykoserocin | 16,640 |
| Amber Mykoserocin | 1,280 |
| Golden Mykoserocin | 1,280 |
| Lime Mykoserocin | 1,280 |
| Malachite Mykoserocin | 1,280 |
| Celadon Mykoserocin | 1,280 |
| Viridian Mykoserocin | 1,280 |
| Azure Cytoserocin | 200 |
| Vermillion Cytoserocin | 200 |

| NPC market good | Required |
|---|---:|
| AV-Composite Molecular Condenser | 436 |
| Isotropic Deposition Guide | 282 |
| AG-Composite Molecular Condenser | 32 |
| LM-Composite Molecular Condenser | 32 |
| CV-Composite Molecular Condenser | 32 |
| Nano Regulation Gate | 20 |
| Counter-Subversion Sensor Array | 10 |
| Nanoscale Filter Plate | 10 |
| Enhanced Electro-Neural Signaller | 10 |
| Meta-Molecular Combiner | 8 |

## Blueprint inventory (live, 2026-11-21)

82 blueprint types — **44 owned, 38 missing** (26 blueprints +
12 reaction formulas). The owned set is byte-for-byte the Hel's:
the prior worlds carry over intact (AIPS, LSBU, CTR, fuel blocks,
the seven simple and nine polymer formulas, the neurolink and
Isotropic Neofullerene formulas the roster already held).

Missing — the Hel's 35 plus four titan components:

| Blueprint | Notes |
|---|---|
| Capital Jump Bridge Array · Capital Clone Vat Bay · Capital Doomsday Weapon Mount · Capital Turret Hardpoint | **titan-specific** — NPC-seeded originals; mineral-heavy builds (millions of Pyerite each) |
| + the Hel's 34 (14 capital BPs · 3 supercapital components · 6 neurolink support · the Ragnarok Blueprint itself · 12 reaction formulas) | the Ragnarok BPC is contract-only (rare-drop origin — the Hel's pin) |

## Mechanics the expansion established

- **The Hel at 4×, plus mineral-volume components**: the titan
  adds no new chain shape — every mechanic the Ragnarok exercises
  exists in a prior chain — but every quantity is a record. This
  is the program's terminal stress test by design: the models that
  survive the Ragnarok survive anything the catalog can express.
- **The reaction era becomes the reaction year**: 27,979 runs =
  350 days at ~10 reactors. Slot count is the binding constraint
  three times over (formulas are cheap; characters are not); the
  plan is fundamentally a **reaction-slot logistics problem** with
  a 71-day build at the end.
- **Titan components are mineral sinks, not reaction sinks**: the
  four titan-specific parts (Jump Bridge, Clone Vat, Doomsday
  Mount, Turret Hardpoint) build from minerals alone — billions of
  Pyerite — so the titan's marginal complexity over the Hel lands
  on procurement, not production. The buy-vs-build and mining
  questions (M10) carry more weight here than anywhere.
- **Recurring commodities at terminal scale**: RCF and Carbon
  Fiber each recur at two levels summing ~4,800 runs — merging
  campaigns is not an optimization at this scale, it is the
  difference between 28,000 runs and ~45,000.
- **The 4-level skill gap**: Capital Ship Construction 5 against
  Octavia's 1 — the longest train the program has modeled, with
  ~4 months of parallel component work to fill it. The
  underleveled-holder state's stress case.

## Findings and caveats

- **Wave shape**: the plan is **~14 months illustrative** — a
  reaction year plus component manufacturing plus the 71-day hull,
  with the mineral mountain's procurement front (1.1B Pyerite is
  months of buying or mining) as the longest acquisition dead zone
  in the program. The mockup's wave bar compresses further than
  the Hel's; the honest rendering is a plan measured in seasons.
- **The one covered mineral**: Tritanium at 30% (97.4M of
  318.8M) — the largest single coverage in the program and still
  a 220M-unit purchase.
- Pins standing: the Ragnarok BPC's drop source (M15), the
  supercapital facility class (M3), reaction-slot semantics (M4/M9
  — binding at triple the Hel's scale), and the merged-campaign
  arithmetic (M5/M9 — priced by the Crash chain, terminal here).
- Skills: Capital Ship Construction 5 simulated (Octavia at 1,
  the sole holder — the underleveled-holder state at maximum);
  every other gate held live.
- The four titan components' BPs are the **last NPC-seeded
  originals** the catalog holds for this world — with them, the
  capital/supercapital/titan BP families are fully enumerated
  across the three chains (Charon, Hel, Ragnarok).
