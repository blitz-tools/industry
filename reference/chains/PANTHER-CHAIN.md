# The Panther chain — full reference

Third chain document (after `TYPHOON-CHAIN.md` and `CHARON-CHAIN.md`),
added 2026-11-19 to stress the models with an **invented T2 (Tech 2)**
target: the invention layer itself (source BPC (Blueprint Copy),
probability, datacores, decryptors), the T1 (Tech 1) hull riding inside
the chain as a build input, capital-component crossover, T2 components
at 1/run volumes, and the advanced moon reactions they consume. Every
deterministic number here is output of the reference scripts —
regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 22440 1
```

Provenance: read from the live SDE (Static Data Export) mirror (release
2026-11-13) and the synced live tables (ownership, skills, stock —
2026-11-19); decryptor modifiers pinned from live ESI (EVE Swagger
Interface) dogma 2026-11-19. Phases count up in build order (terminators
= phase 0, target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Panther ×1)

- IDs: Panther **22440**, Panther Blueprint **22441** (maxProductionLimit
  1), invented from Typhoon Blueprint **998** (maxProductionLimit 10) at
  **22% base probability** (`industryActivityProbabilities`).
- The chain **contains the entire Typhoon chain**: the T1 hull (×1) is a
  direct manufacturing input, so the Typhoon's component/reaction stack
  rides at phases 5–0, interleaved with the T2 layers by depth — not
  nested inside them.
- Capital crossover: **Capital Jump Drive ×3** (maxProductionLimit 40) —
  Wetware Mainframe (tier-4 PI (Planetary Industry)) + Reinforced Carbon
  Fiber + minerals. The Charon's capital-component world inside a
  sub-capital hull.
- **T2 components ×7 types at 1 unit/run**: the Fernite Carbide Composite
  Armor Plate alone is 18,750 runs (maxProductionLimit 20,000 — one job
  can hold them all, ≈125 h unskilled). Their blueprints are NPC-seeded
  originals with **no producer in the SDE** — the acquisition story
  inverts the Charon's contract-backfill: buy cheap BPOs (Blueprint
  Originals) on the market.
- **Invention**: 53.33 h per attempt; expected 4.55 attempts for one
  success → ≈10.2 d serialized on one character (the roster's only
  inventor). 64 datacores per attempt (32 + 32); expected ≈145 of each
  per success — on hand: 53 and 11.
- Panther build: 100 h (4.17 d). Fuel blocks recur at phases 1–3 (as in
  the Charon chain). Construction Blocks ×450 and Morphite ×900 are
  direct hull inputs and terminators.

## Per-branch tree (Panther ×1)

Every branch, shared intermediates repeated per parent — 1175
lines, the widest chain in the reference set:

```text
- Panther x1 [manufacturing] (1 runs, 1/run)
  - Typhoon x1 [manufacturing] (1 runs, 1/run)
    - Core Temperature Regulator x1 [manufacturing] (1 runs, 1/run)
      - Chiral Structures x100  [raw]
      - Water x100  [raw]
      - Pressurized Oxidizers x500 [reaction] (3 runs, 200/run)
        - Carbon Polymers x600 [reaction] (3 runs, 200/run)
          - Helium Fuel Block x15 [manufacturing] (1 runs, 40/run)
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
          - Nitrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
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
        - Oxy-Organic Solvents x3 [reaction] (1 runs, 10/run)
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
      - Reinforced Carbon Fiber x500 [reaction] (3 runs, 200/run)
        - Carbon Fiber x600 [reaction] (3 runs, 200/run)
          - Hydrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
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
        - Oxy-Organic Solvents x3 [reaction] (1 runs, 10/run)
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
        - Thermosetting Polymer x600 [reaction] (3 runs, 200/run)
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
          - Atmospheric Gases x300  [raw]
          - Silicates x300  [raw]
    - Life Support Backup Unit x75 [manufacturing] (25 runs, 3/run)
      - Test Cultures x200  [raw]
      - Viral Agent x200  [raw]
      - Reinforced Carbon Fiber x250 [reaction] (2 runs, 200/run)
        - Carbon Fiber x400 [reaction] (2 runs, 200/run)
          - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
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
        - Oxy-Organic Solvents x2 [reaction] (1 runs, 10/run)
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
        - Thermosetting Polymer x400 [reaction] (2 runs, 200/run)
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
          - Atmospheric Gases x200  [raw]
          - Silicates x200  [raw]
    - Auto-Integrity Preservation Seal x150 [manufacturing] (50 runs, 3/run)
      - Supertensile Plastics x200  [raw]
      - Nanites x200  [raw]
      - Reinforced Carbon Fiber x500 [reaction] (3 runs, 200/run)
        - Carbon Fiber x600 [reaction] (3 runs, 200/run)
          - Hydrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
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
        - Oxy-Organic Solvents x3 [reaction] (1 runs, 10/run)
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
        - Thermosetting Polymer x600 [reaction] (3 runs, 200/run)
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
          - Atmospheric Gases x300  [raw]
          - Silicates x300  [raw]
    - Megacyte x1,950  [raw]
    - Zydrine x3,900  [raw]
    - Nocxium x15,600  [raw]
    - Isogen x130,000  [raw]
    - Mexallon x390,000  [raw]
    - Pyerite x2,600,000  [raw]
    - Tritanium x5,200,000  [raw]
  - Capital Jump Drive x3 [manufacturing] (3 runs, 1/run)
    - Wetware Mainframe x3  [raw]
    - Reinforced Carbon Fiber x300 [reaction] (2 runs, 200/run)
      - Carbon Fiber x400 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
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
      - Oxy-Organic Solvents x2 [reaction] (1 runs, 10/run)
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
      - Thermosetting Polymer x400 [reaction] (2 runs, 200/run)
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
        - Atmospheric Gases x200  [raw]
        - Silicates x200  [raw]
    - Megacyte x1,260  [raw]
    - Zydrine x2,700  [raw]
    - Nocxium x5,064  [raw]
    - Isogen x50,625  [raw]
    - Tritanium x180,000  [raw]
    - Mexallon x180,000  [raw]
    - Pyerite x648,000  [raw]
  - R.A.M.- Starship Tech x30 [manufacturing] (1 runs, 100/run)
    - Tritanium x556  [raw]
    - Pyerite x444  [raw]
    - Mexallon x222  [raw]
    - Isogen x82  [raw]
    - Nocxium x36  [raw]
  - Plasma Thruster x225 [manufacturing] (225 runs, 1/run)
    - Phenolic Composites x675 [reaction] (1 runs, 2200/run)
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
      - Silicon Diborite x100 [reaction] (1 runs, 200/run)
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
        - Evaporite Deposits x100  [raw]
        - Silicates x100  [raw]
      - Caesarium Cadmide x100 [reaction] (1 runs, 200/run)
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
        - Cadmium x100  [raw]
        - Caesium x100  [raw]
      - Vanadium Hafnite x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Vanadium x100  [raw]
        - Hafnium x100  [raw]
    - Fernite Carbide x2,925 [reaction] (1 runs, 10000/run)
      - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Fernite Alloy x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Scandium x100  [raw]
        - Vanadium x100  [raw]
      - Ceramic Powder x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x100  [raw]
        - Silicates x100  [raw]
    - Ferrogel x225 [reaction] (1 runs, 400/run)
      - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Hexite x100 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Chromium x100  [raw]
        - Platinum x100  [raw]
      - Hyperflurite x100 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Vanadium x100  [raw]
        - Promethium x100  [raw]
      - Ferrofluid x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hafnium x100  [raw]
        - Dysprosium x100  [raw]
      - Prometium x100 [reaction] (1 runs, 200/run)
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
        - Cadmium x100  [raw]
        - Promethium x100  [raw]
  - Construction Blocks x450  [raw]
  - Nuclear Reactor Unit x450 [manufacturing] (450 runs, 1/run)
    - Fernite Carbide x4,050 [reaction] (1 runs, 10000/run)
      - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Fernite Alloy x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Scandium x100  [raw]
        - Vanadium x100  [raw]
      - Ceramic Powder x100 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x100  [raw]
        - Silicates x100  [raw]
    - Fermionic Condensates x900 [reaction] (5 runs, 200/run)
      - Helium Fuel Block x25 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Helium Isotopes x450  [raw]
      - Caesarium Cadmide x500 [reaction] (3 runs, 200/run)
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
        - Cadmium x300  [raw]
        - Caesium x300  [raw]
      - Dysporite x500 [reaction] (3 runs, 200/run)
        - Helium Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x300  [raw]
        - Dysprosium x300  [raw]
      - Fluxed Condensates x500 [reaction] (3 runs, 200/run)
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
        - Neodymium x300  [raw]
        - Thulium x300  [raw]
      - Prometium x500 [reaction] (3 runs, 200/run)
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
        - Cadmium x300  [raw]
        - Promethium x300  [raw]
  - Morphite x900  [raw]
  - Ladar Sensor Cluster x900 [manufacturing] (900 runs, 1/run)
    - Fernite Carbide x19,800 [reaction] (2 runs, 10000/run)
      - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Hydrogen Isotopes x450  [raw]
      - Fernite Alloy x200 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Scandium x100  [raw]
        - Vanadium x100  [raw]
      - Ceramic Powder x200 [reaction] (1 runs, 200/run)
        - Hydrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x100  [raw]
        - Silicates x100  [raw]
    - Hypersynaptic Fibers x1,800 [reaction] (3 runs, 750/run)
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
      - Solerium x300 [reaction] (2 runs, 200/run)
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
        - Chromium x200  [raw]
        - Caesium x200  [raw]
      - Dysporite x300 [reaction] (2 runs, 200/run)
        - Helium Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x200  [raw]
        - Dysprosium x200  [raw]
      - Vanadium Hafnite x300 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Vanadium x200  [raw]
        - Hafnium x200  [raw]
    - Nanotransistors x900 [reaction] (1 runs, 1500/run)
      - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Nitrogen Isotopes x450  [raw]
      - Sulfuric Acid x100 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Atmospheric Gases x100  [raw]
        - Evaporite Deposits x100  [raw]
      - Platinum Technite x100 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Platinum x100  [raw]
        - Technetium x100  [raw]
      - Neo Mercurite x100 [reaction] (1 runs, 200/run)
        - Helium Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x100  [raw]
        - Neodymium x100  [raw]
  - Deflection Shield Emitter x1,634 [manufacturing] (1,634 runs, 1/run)
    - Fernite Carbide x35,948 [reaction] (4 runs, 10000/run)
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
      - Fernite Alloy x400 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Scandium x200  [raw]
        - Vanadium x200  [raw]
      - Ceramic Powder x400 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x200  [raw]
        - Silicates x200  [raw]
    - Ferrogel x1,634 [reaction] (5 runs, 400/run)
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
      - Hexite x500 [reaction] (3 runs, 200/run)
        - Nitrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Chromium x300  [raw]
        - Platinum x300  [raw]
      - Hyperflurite x500 [reaction] (3 runs, 200/run)
        - Nitrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Vanadium x300  [raw]
        - Promethium x300  [raw]
      - Ferrofluid x500 [reaction] (3 runs, 200/run)
        - Hydrogen Fuel Block x15 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Hafnium x300  [raw]
        - Dysprosium x300  [raw]
      - Prometium x500 [reaction] (3 runs, 200/run)
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
        - Cadmium x300  [raw]
        - Promethium x300  [raw]
    - Sylramic Fibers x14,706 [reaction] (3 runs, 6000/run)
      - Helium Fuel Block x15 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Helium Isotopes x450  [raw]
      - Ceramic Powder x300 [reaction] (2 runs, 200/run)
        - Hydrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x200  [raw]
        - Silicates x200  [raw]
      - Hexite x300 [reaction] (2 runs, 200/run)
        - Nitrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Chromium x200  [raw]
        - Platinum x200  [raw]
  - Electrolytic Capacitor Unit x2,250 [manufacturing] (2,250 runs, 1/run)
    - Fernite Carbide x60,750 [reaction] (7 runs, 10000/run)
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
      - Fernite Alloy x700 [reaction] (4 runs, 200/run)
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
        - Scandium x400  [raw]
        - Vanadium x400  [raw]
      - Ceramic Powder x700 [reaction] (4 runs, 200/run)
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
        - Evaporite Deposits x400  [raw]
        - Silicates x400  [raw]
    - Nanotransistors x2,250 [reaction] (2 runs, 1500/run)
      - Nitrogen Fuel Block x10 [manufacturing] (1 runs, 40/run)
        - Robotics x1  [raw]
        - Enriched Uranium x4  [raw]
        - Mechanical Parts x4  [raw]
        - Coolant x9  [raw]
        - Strontium Clathrates x20  [raw]
        - Oxygen x22  [raw]
        - Heavy Water x170  [raw]
        - Liquid Ozone x350  [raw]
        - Nitrogen Isotopes x450  [raw]
      - Sulfuric Acid x200 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Atmospheric Gases x100  [raw]
        - Evaporite Deposits x100  [raw]
      - Platinum Technite x200 [reaction] (1 runs, 200/run)
        - Nitrogen Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Platinum x100  [raw]
        - Technetium x100  [raw]
      - Neo Mercurite x200 [reaction] (1 runs, 200/run)
        - Helium Fuel Block x5 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x100  [raw]
        - Neodymium x100  [raw]
    - Plasmonic Metamaterials x4,500 [reaction] (15 runs, 300/run)
      - Hydrogen Fuel Block x75 [manufacturing] (2 runs, 40/run)
        - Robotics x2  [raw]
        - Enriched Uranium x8  [raw]
        - Mechanical Parts x8  [raw]
        - Coolant x18  [raw]
        - Strontium Clathrates x40  [raw]
        - Oxygen x44  [raw]
        - Heavy Water x340  [raw]
        - Liquid Ozone x700  [raw]
        - Hydrogen Isotopes x900  [raw]
      - Fernite Alloy x1,500 [reaction] (8 runs, 200/run)
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
        - Scandium x800  [raw]
        - Vanadium x800  [raw]
      - Neo Mercurite x1,500 [reaction] (8 runs, 200/run)
        - Helium Fuel Block x40 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x800  [raw]
        - Neodymium x800  [raw]
    - Fullerides x24,750 [reaction] (9 runs, 3000/run)
      - Nitrogen Fuel Block x45 [manufacturing] (2 runs, 40/run)
        - Robotics x2  [raw]
        - Enriched Uranium x8  [raw]
        - Mechanical Parts x8  [raw]
        - Coolant x18  [raw]
        - Strontium Clathrates x40  [raw]
        - Oxygen x44  [raw]
        - Heavy Water x340  [raw]
        - Liquid Ozone x700  [raw]
        - Nitrogen Isotopes x900  [raw]
      - Carbon Polymers x900 [reaction] (5 runs, 200/run)
        - Helium Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Hydrocarbons x500  [raw]
        - Silicates x500  [raw]
      - Platinum Technite x900 [reaction] (5 runs, 200/run)
        - Nitrogen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Platinum x500  [raw]
        - Technetium x500  [raw]
  - Nanomechanical Microprocessor x6,300 [manufacturing] (6,300 runs, 1/run)
    - Phenolic Composites x37,800 [reaction] (18 runs, 2200/run)
      - Oxygen Fuel Block x90 [manufacturing] (3 runs, 40/run)
        - Robotics x3  [raw]
        - Enriched Uranium x12  [raw]
        - Mechanical Parts x12  [raw]
        - Coolant x27  [raw]
        - Strontium Clathrates x60  [raw]
        - Oxygen x66  [raw]
        - Heavy Water x510  [raw]
        - Liquid Ozone x1,050  [raw]
        - Oxygen Isotopes x1,350  [raw]
      - Silicon Diborite x1,800 [reaction] (9 runs, 200/run)
        - Oxygen Fuel Block x45 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Evaporite Deposits x900  [raw]
        - Silicates x900  [raw]
      - Caesarium Cadmide x1,800 [reaction] (9 runs, 200/run)
        - Oxygen Fuel Block x45 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Oxygen Isotopes x900  [raw]
        - Cadmium x900  [raw]
        - Caesium x900  [raw]
      - Vanadium Hafnite x1,800 [reaction] (9 runs, 200/run)
        - Hydrogen Fuel Block x45 [manufacturing] (2 runs, 40/run)
          - Robotics x2  [raw]
          - Enriched Uranium x8  [raw]
          - Mechanical Parts x8  [raw]
          - Coolant x18  [raw]
          - Strontium Clathrates x40  [raw]
          - Oxygen x44  [raw]
          - Heavy Water x340  [raw]
          - Liquid Ozone x700  [raw]
          - Hydrogen Isotopes x900  [raw]
        - Vanadium x900  [raw]
        - Hafnium x900  [raw]
    - Fernite Carbide x107,100 [reaction] (11 runs, 10000/run)
      - Hydrogen Fuel Block x55 [manufacturing] (2 runs, 40/run)
        - Robotics x2  [raw]
        - Enriched Uranium x8  [raw]
        - Mechanical Parts x8  [raw]
        - Coolant x18  [raw]
        - Strontium Clathrates x40  [raw]
        - Oxygen x44  [raw]
        - Heavy Water x340  [raw]
        - Liquid Ozone x700  [raw]
        - Hydrogen Isotopes x900  [raw]
      - Fernite Alloy x1,100 [reaction] (6 runs, 200/run)
        - Hydrogen Fuel Block x30 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Scandium x600  [raw]
        - Vanadium x600  [raw]
      - Ceramic Powder x1,100 [reaction] (6 runs, 200/run)
        - Hydrogen Fuel Block x30 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Hydrogen Isotopes x450  [raw]
        - Evaporite Deposits x600  [raw]
        - Silicates x600  [raw]
    - Plasmonic Metamaterials x12,600 [reaction] (42 runs, 300/run)
      - Hydrogen Fuel Block x210 [manufacturing] (6 runs, 40/run)
        - Robotics x6  [raw]
        - Enriched Uranium x24  [raw]
        - Mechanical Parts x24  [raw]
        - Coolant x54  [raw]
        - Strontium Clathrates x120  [raw]
        - Oxygen x132  [raw]
        - Heavy Water x1,020  [raw]
        - Liquid Ozone x2,100  [raw]
        - Hydrogen Isotopes x2,700  [raw]
      - Fernite Alloy x4,200 [reaction] (21 runs, 200/run)
        - Hydrogen Fuel Block x105 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Hydrogen Isotopes x1,350  [raw]
        - Scandium x2,100  [raw]
        - Vanadium x2,100  [raw]
      - Neo Mercurite x4,200 [reaction] (21 runs, 200/run)
        - Helium Fuel Block x105 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Helium Isotopes x1,350  [raw]
        - Mercury x2,100  [raw]
        - Neodymium x2,100  [raw]
    - Nanotransistors x12,600 [reaction] (9 runs, 1500/run)
      - Nitrogen Fuel Block x45 [manufacturing] (2 runs, 40/run)
        - Robotics x2  [raw]
        - Enriched Uranium x8  [raw]
        - Mechanical Parts x8  [raw]
        - Coolant x18  [raw]
        - Strontium Clathrates x40  [raw]
        - Oxygen x44  [raw]
        - Heavy Water x340  [raw]
        - Liquid Ozone x700  [raw]
        - Nitrogen Isotopes x900  [raw]
      - Sulfuric Acid x900 [reaction] (5 runs, 200/run)
        - Nitrogen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Atmospheric Gases x500  [raw]
        - Evaporite Deposits x500  [raw]
      - Platinum Technite x900 [reaction] (5 runs, 200/run)
        - Nitrogen Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Nitrogen Isotopes x450  [raw]
        - Platinum x500  [raw]
        - Technetium x500  [raw]
      - Neo Mercurite x900 [reaction] (5 runs, 200/run)
        - Helium Fuel Block x25 [manufacturing] (1 runs, 40/run)
          - Robotics x1  [raw]
          - Enriched Uranium x4  [raw]
          - Mechanical Parts x4  [raw]
          - Coolant x9  [raw]
          - Strontium Clathrates x20  [raw]
          - Oxygen x22  [raw]
          - Heavy Water x170  [raw]
          - Liquid Ozone x350  [raw]
          - Helium Isotopes x450  [raw]
        - Mercury x500  [raw]
        - Neodymium x500  [raw]
  - Fernite Carbide Composite Armor Plate x18,750 [manufacturing] (18,750 runs, 1/run)
    - Fernite Carbide x825,000 [reaction] (83 runs, 10000/run)
      - Hydrogen Fuel Block x415 [manufacturing] (11 runs, 40/run)
        - Robotics x11  [raw]
        - Enriched Uranium x44  [raw]
        - Mechanical Parts x44  [raw]
        - Coolant x99  [raw]
        - Strontium Clathrates x220  [raw]
        - Oxygen x242  [raw]
        - Heavy Water x1,870  [raw]
        - Liquid Ozone x3,850  [raw]
        - Hydrogen Isotopes x4,950  [raw]
      - Fernite Alloy x8,300 [reaction] (42 runs, 200/run)
        - Hydrogen Fuel Block x210 [manufacturing] (6 runs, 40/run)
          - Robotics x6  [raw]
          - Enriched Uranium x24  [raw]
          - Mechanical Parts x24  [raw]
          - Coolant x54  [raw]
          - Strontium Clathrates x120  [raw]
          - Oxygen x132  [raw]
          - Heavy Water x1,020  [raw]
          - Liquid Ozone x2,100  [raw]
          - Hydrogen Isotopes x2,700  [raw]
        - Scandium x4,200  [raw]
        - Vanadium x4,200  [raw]
      - Ceramic Powder x8,300 [reaction] (42 runs, 200/run)
        - Hydrogen Fuel Block x210 [manufacturing] (6 runs, 40/run)
          - Robotics x6  [raw]
          - Enriched Uranium x24  [raw]
          - Mechanical Parts x24  [raw]
          - Coolant x54  [raw]
          - Strontium Clathrates x120  [raw]
          - Oxygen x132  [raw]
          - Heavy Water x1,020  [raw]
          - Liquid Ozone x2,100  [raw]
          - Hydrogen Isotopes x2,700  [raw]
        - Evaporite Deposits x4,200  [raw]
        - Silicates x4,200  [raw]
    - Sylramic Fibers x206,250 [reaction] (35 runs, 6000/run)
      - Helium Fuel Block x175 [manufacturing] (5 runs, 40/run)
        - Robotics x5  [raw]
        - Enriched Uranium x20  [raw]
        - Mechanical Parts x20  [raw]
        - Coolant x45  [raw]
        - Strontium Clathrates x100  [raw]
        - Oxygen x110  [raw]
        - Heavy Water x850  [raw]
        - Liquid Ozone x1,750  [raw]
        - Helium Isotopes x2,250  [raw]
      - Ceramic Powder x3,500 [reaction] (18 runs, 200/run)
        - Hydrogen Fuel Block x90 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Hydrogen Isotopes x1,350  [raw]
        - Evaporite Deposits x1,800  [raw]
        - Silicates x1,800  [raw]
      - Hexite x3,500 [reaction] (18 runs, 200/run)
        - Nitrogen Fuel Block x90 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Nitrogen Isotopes x1,350  [raw]
        - Chromium x1,800  [raw]
        - Platinum x1,800  [raw]
```

## Aggregated phases (shared intermediates merged)

Same-type requirements merge per phase, then round runs once. Seven
phases — matching the Charon's depth with a different composition:
phase 5 mixes the T1 hull, all seven T2 components, the capital jump
drives, and two raw terminators (Construction Blocks, Morphite) as
direct hull inputs.

### Phase 6

| Type | Required | Activity / runs |
|---|---:|---|
| Panther | 1 | manufacturing, 1 runs |

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Construction Blocks | 450 | raw (terminator) |
| Morphite | 900 | raw (terminator) |
| Typhoon | 1 | manufacturing, 1 runs |
| R.A.M.- Starship Tech | 30 | manufacturing, 1 runs |
| Plasma Thruster | 225 | manufacturing, 225 runs |
| Ladar Sensor Cluster | 900 | manufacturing, 900 runs |
| Nanomechanical Microprocessor | 6,300 | manufacturing, 6,300 runs |
| Fernite Carbide Composite Armor Plate | 18,750 | manufacturing, 18,750 runs |
| Nuclear Reactor Unit | 450 | manufacturing, 450 runs |
| Electrolytic Capacitor Unit | 2,250 | manufacturing, 2,250 runs |
| Deflection Shield Emitter | 1,634 | manufacturing, 1,634 runs |
| Capital Jump Drive | 3 | manufacturing, 3 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Megacyte | 3,210 | raw (terminator) |
| Zydrine | 6,600 | raw (terminator) |
| Nocxium | 20,700 | raw (terminator) |
| Isogen | 180,707 | raw (terminator) |
| Mexallon | 570,222 | raw (terminator) |
| Pyerite | 3,248,444 | raw (terminator) |
| Tritanium | 5,380,556 | raw (terminator) |
| Wetware Mainframe | 3 | raw (terminator) |
| Fernite Carbide | 1,055,573 | reaction, 106 runs |
| Sylramic Fibers | 220,956 | reaction, 37 runs |
| Fullerides | 24,750 | reaction, 9 runs |
| Phenolic Composites | 38,475 | reaction, 18 runs |
| Nanotransistors | 15,750 | reaction, 11 runs |
| Hypersynaptic Fibers | 1,800 | reaction, 3 runs |
| Ferrogel | 1,859 | reaction, 5 runs |
| Fermionic Condensates | 900 | reaction, 5 runs |
| Plasmonic Metamaterials | 17,100 | reaction, 57 runs |
| Reinforced Carbon Fiber | 300 | reaction, 2 runs |
| Auto-Integrity Preservation Seal | 150 | manufacturing, 50 runs |
| Core Temperature Regulator | 1 | manufacturing, 1 runs |
| Life Support Backup Unit | 75 | manufacturing, 25 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Chiral Structures | 100 | raw (terminator) |
| Water | 100 | raw (terminator) |
| Test Cultures | 200 | raw (terminator) |
| Viral Agent | 200 | raw (terminator) |
| Supertensile Plastics | 200 | raw (terminator) |
| Nanites | 200 | raw (terminator) |
| Nitrogen Fuel Block | 100 | manufacturing, 3 runs |
| Hydrogen Fuel Block | 840 | manufacturing, 21 runs |
| Helium Fuel Block | 210 | manufacturing, 6 runs |
| Oxygen Fuel Block | 105 | manufacturing, 3 runs |
| Fernite Alloy | 16,300 | reaction, 82 runs |
| Silicon Diborite | 1,800 | reaction, 9 runs |
| Carbon Polymers | 900 | reaction, 5 runs |
| Ceramic Powder | 14,300 | reaction, 72 runs |
| Sulfuric Acid | 1,100 | reaction, 6 runs |
| Platinum Technite | 2,000 | reaction, 10 runs |
| Caesarium Cadmide | 2,300 | reaction, 12 runs |
| Solerium | 300 | reaction, 2 runs |
| Hexite | 4,200 | reaction, 21 runs |
| Hyperflurite | 500 | reaction, 3 runs |
| Neo Mercurite | 6,800 | reaction, 34 runs |
| Dysporite | 800 | reaction, 4 runs |
| Ferrofluid | 500 | reaction, 3 runs |
| Fluxed Condensates | 500 | reaction, 3 runs |
| Vanadium Hafnite | 2,100 | reaction, 11 runs |
| Prometium | 1,000 | reaction, 5 runs |
| Carbon Fiber | 400 | reaction, 2 runs |
| Oxy-Organic Solvents | 2 | reaction, 1 runs |
| Thermosetting Polymer | 400 | reaction, 2 runs |
| Pressurized Oxidizers | 500 | reaction, 3 runs |
| Reinforced Carbon Fiber | 1,250 | reaction, 7 runs |

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrocarbons | 2,700 | raw (terminator) |
| Evaporite Deposits | 8,900 | raw (terminator) |
| Atmospheric Gases | 2,800 | raw (terminator) |
| Silicates | 8,800 | raw (terminator) |
| Robotics | 33 | raw (terminator) |
| Enriched Uranium | 132 | raw (terminator) |
| Mechanical Parts | 132 | raw (terminator) |
| Coolant | 297 | raw (terminator) |
| Strontium Clathrates | 660 | raw (terminator) |
| Oxygen | 726 | raw (terminator) |
| Heavy Water | 5,610 | raw (terminator) |
| Liquid Ozone | 11,550 | raw (terminator) |
| Oxygen Isotopes | 1,350 | raw (terminator) |
| Cadmium | 1,700 | raw (terminator) |
| Caesium | 1,400 | raw (terminator) |
| Vanadium | 9,600 | raw (terminator) |
| Hafnium | 1,400 | raw (terminator) |
| Hydrogen Isotopes | 9,450 | raw (terminator) |
| Scandium | 8,200 | raw (terminator) |
| Chromium | 2,300 | raw (terminator) |
| Platinum | 3,100 | raw (terminator) |
| Promethium | 800 | raw (terminator) |
| Dysprosium | 700 | raw (terminator) |
| Helium Isotopes | 2,700 | raw (terminator) |
| Mercury | 3,800 | raw (terminator) |
| Neodymium | 3,700 | raw (terminator) |
| Thulium | 300 | raw (terminator) |
| Nitrogen Isotopes | 1,350 | raw (terminator) |
| Technetium | 1,000 | raw (terminator) |
| Nitrogen Fuel Block | 200 | manufacturing, 5 runs |
| Hydrogen Fuel Block | 850 | manufacturing, 22 runs |
| Helium Fuel Block | 215 | manufacturing, 6 runs |
| Oxygen Fuel Block | 170 | manufacturing, 5 runs |
| Carbon Polymers | 600 | reaction, 3 runs |
| Sulfuric Acid | 600 | reaction, 3 runs |
| Carbon Fiber | 1,400 | reaction, 7 runs |
| Oxy-Organic Solvents | 10 | reaction, 1 runs |
| Thermosetting Polymer | 1,400 | reaction, 7 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrocarbons | 3,000 | raw (terminator) |
| Silicates | 1,000 | raw (terminator) |
| Atmospheric Gases | 3,000 | raw (terminator) |
| Evaporite Deposits | 1,000 | raw (terminator) |
| Robotics | 38 | raw (terminator) |
| Enriched Uranium | 152 | raw (terminator) |
| Mechanical Parts | 152 | raw (terminator) |
| Coolant | 342 | raw (terminator) |
| Strontium Clathrates | 760 | raw (terminator) |
| Oxygen | 836 | raw (terminator) |
| Heavy Water | 6,460 | raw (terminator) |
| Liquid Ozone | 13,300 | raw (terminator) |
| Hydrogen Isotopes | 9,900 | raw (terminator) |
| Oxygen Isotopes | 2,250 | raw (terminator) |
| Nitrogen Isotopes | 2,250 | raw (terminator) |
| Helium Isotopes | 2,700 | raw (terminator) |
| Nitrogen Fuel Block | 15 | manufacturing, 1 runs |
| Hydrogen Fuel Block | 35 | manufacturing, 1 runs |
| Helium Fuel Block | 15 | manufacturing, 1 runs |
| Oxygen Fuel Block | 40 | manufacturing, 1 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 4 | raw (terminator) |
| Enriched Uranium | 16 | raw (terminator) |
| Mechanical Parts | 16 | raw (terminator) |
| Coolant | 36 | raw (terminator) |
| Strontium Clathrates | 80 | raw (terminator) |
| Oxygen | 88 | raw (terminator) |
| Heavy Water | 680 | raw (terminator) |
| Liquid Ozone | 1,400 | raw (terminator) |
| Helium Isotopes | 450 | raw (terminator) |
| Nitrogen Isotopes | 450 | raw (terminator) |
| Oxygen Isotopes | 450 | raw (terminator) |
| Hydrogen Isotopes | 450 | raw (terminator) |

## Raw-material acquisition table (Panther ×1)

Chain terminators summed across all stages, grouped by category. New
versus the Charon: four more moon materials (Vanadium, Scandium,
Platinum, Technetium), Morphite (the top moon material — the SDE files
it under the *Mineral* group, so the name-list fallback owns it), and
Construction Blocks as an NPC-seeded market good (no blueprint exists).
Datacores and decryptors are invention-layer inputs and live in their
own section below — deliberately kept out of this deterministic table.

### Minerals

| Type | Required |
|---|---:|
| Tritanium | 5,380,556 |
| Pyerite | 3,248,444 |
| Mexallon | 570,222 |
| Isogen | 180,707 |
| Nocxium | 20,700 |
| Zydrine | 6,600 |
| Megacyte | 3,210 |

### Moon materials

| Type | Required |
|---|---:|
| Evaporite Deposits | 9,900 |
| Silicates | 9,800 |
| Vanadium | 9,600 |
| Scandium | 8,200 |
| Atmospheric Gases | 5,800 |
| Hydrocarbons | 5,700 |
| Mercury | 3,800 |
| Neodymium | 3,700 |
| Platinum | 3,100 |
| Chromium | 2,300 |
| Cadmium | 1,700 |
| Caesium | 1,400 |
| Hafnium | 1,400 |
| Technetium | 1,000 |
| Morphite | 900 |
| Promethium | 800 |
| Dysprosium | 700 |
| Thulium | 300 |

### Pi commodities

| Type | Required |
|---|---:|
| Coolant | 675 |
| Enriched Uranium | 300 |
| Mechanical Parts | 300 |
| Test Cultures | 200 |
| Viral Agent | 200 |
| Supertensile Plastics | 200 |
| Nanites | 200 |
| Chiral Structures | 100 |
| Water | 100 |
| Robotics | 75 |
| Wetware Mainframe | 3 |

### Ice products

| Type | Required |
|---|---:|
| Liquid Ozone | 26,250 |
| Hydrogen Isotopes | 19,800 |
| Heavy Water | 12,750 |
| Helium Isotopes | 5,850 |
| Nitrogen Isotopes | 4,050 |
| Oxygen Isotopes | 4,050 |
| Oxygen | 1,650 |
| Strontium Clathrates | 1,500 |

### Npc market goods

| Type | Required |
|---|---:|
| Construction Blocks | 450 |

## Invention layer (Panther Blueprint)

The invention overlay — not part of the material walk above. The
Panther Blueprint's *build* inputs resolved normally in the tree; this
is how the blueprint itself is acquired.

- **Source**: Typhoon Blueprint (blueprint 998, invention activity 8)
- **Base probability**: 22% (SDE; skill levels assumed NOT to
  modify it post-Crius — pin at M8)
- **Materials per attempt**: 32× Datacore - Minmatar Starship Engineering, 32× Datacore - High Energy Physics
- **Skills**: High Energy Physics 1, Minmatar Starship Engineering 1, Minmatar Encryption Methods 1 — live check 2026-11-19: **only blitzrage holds all three** (4 / 4 / 1); invention jobs serialize onto one character
- **T1 consumption**: 1 run of the source BPC per attempt — implicit in
  the game, absent from the SDE material list. The pool holds 10 Typhoon
  BPCs / 52 runs: ≈11 expected successes of fuel
- **Duration**: 53.33 h per attempt (activity 8 on the Typhoon
  Blueprint); expected ≈10.2 d serialized for one success

Expected-value math (no decryptor): attempts per success = 1/p = 4.55;
expected datacores per success ≈ 145 of each type. Confidence for
at least one success in n attempts, P = 1 − 0.78ⁿ:

| Attempts n | 4 | 7 | 10 | 15 |
|---|---:|---:|---:|---:|
| P(≥1 success) | 63% | 82% | 92% | 98% |

### Decryptor scenarios

Modifiers pinned from live ESI dogma 2026-11-19 (not in the SDE mirror —
`DECRYPTORS` in `chain_expand.py` carries the provenance). The invented
BPC's base ME (Material Efficiency) / TE (Time Efficiency) is community-
documented at −4 / −4 and is **not** in SDE/ESI — pin at M8. Runs = ship
base 1 + max-run modifier; more runs per BPC mean fewer inventions per
ship at scale (module base runs differ — pin at M8). Live decryptor
stock 2026-11-19: all eight types held, 125 units total.

| Decryptor | p_eff | E[attempts] | E[datacores] | ME mod | ME_eff | TE | runs/BPC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Accelerant | 0.26 | 3.79 | 121 each | +2 | −2 | +10 | 2 |
| Attainment | 0.40 | 2.53 | 81 each | −1 | −5 | +4 | 5 |
| Augmentation | 0.13 | 7.58 | 242 each | −2 | −6 | +2 | 10 |
| Parity | 0.33 | 3.03 | 97 each | +1 | −3 | −2 | 4 |
| Process | 0.24 | 4.13 | 132 each | +3 | −1 | +6 | 1 |
| Symmetry | 0.22 | 4.55 | 145 each | +1 | −3 | +8 | 3 |
| Optimized Attainment | 0.42 | 2.39 | 77 each | +1 | −3 | −2 | 3 |
| Optimized Augmentation | 0.20 | 5.05 | 162 each | +2 | −2 | +0 | 8 |

ME_eff = the invented BPC's resulting ME (assumed base −4 + the
decryptor's modifier — the base is the M8 pin). It multiplies the
**entire ship bill** — every T2 component and mineral the Panther
build consumes.

Reading the table: Optimized Attainment nearly doubles the base chance
(0.42, ≈2.4 attempts) at ME_eff −3; Attainment is the cheap probability
play (0.40) but lands at ME_eff −5; Process maximizes material
efficiency (ME_eff −1) at a slightly reduced chance; Augmentation
trades more than half the probability for +9 runs per BPC — a scale
play, wrong for a ×1 target.

### Decision axes (deterministic, pre-pricing)

Which decryptor to use is a two-axis trade the planner can quantify
before any isk math (M10) exists — whether that comparison happens in
the planner UI is the recorded M8 question (fixed choice per plan vs
comparing EVs):

- **Time axis** — expected attempts × 53.33 h, serialized on the sole
  inventor: Optimized Attainment ≈ 2.4 attempts ≈ 128 h; no decryptor
  ≈ 4.5 ≈ 243 h; Augmentation ≈ 7.6 ≈ 404 h. The full spread between
  the best and worst probability decryptor is ≈ 5.2 attempts ≈ 277 h
  and ≈ 330 datacores.
- **Material axis** — the invented BPC's ME_eff multiplies the whole
  ship bill. Working model: 1 ME point ≈ 1% of materials (exact
  rounding is M4's pin). No decryptor → ME_eff −4 → ≈ +4% materials;
  Process → −1 → ≈ +1%; Accelerant / Optimized Augmentation → −2 →
  ≈ +2%; Parity / Symmetry / Optimized Attainment → −3 → ≈ +3%;
  Attainment → −5 → ≈ +5%; Augmentation → −6 → ≈ +6%.

At Panther ×1 scale the material axis dominates everything the time
axis can offer: one ME point ≈ 1% of 18,750 armor plates + 5.4M
Tritanium + 900 Morphite + the rest of the bill, while the entire
time-axis spread is ≈ 277 h of one character's invention slots.
Concretely: choosing Process over Optimized Attainment costs ≈ 1.7
more attempts (≈ 93 h) and ≈ 55 more datacores of each type, and saves
≈ 2% of the entire ship bill. The isk-optimal answer still needs M10
(decryptor and datacore prices against material prices), but the
structure is fixed: **probability decryptors buy wall time, ME
decryptors buy the bill — and at T2 volumes the bill is the bigger
number.**

### Parallel invention branch (wave composition)

The invented BPC gates exactly one node — the final ship build — so
invention is a parallel branch of the dependency graph, not a phase:
attempts install in wave 1 alongside the fuel-block and first
reaction jobs, per the wave-membership rule (waves mix phases and
activities freely).

Wall-time shapes at ×1:

| Branch | Duration | Notes |
|---|---:|---|
| Material chain below the ship | ≈6–8 d | two ≈5.5 d max-run component jobs (armor plate 130.2 h, microprocessor 131.2 h) + their reaction inputs; the Typhoon hull sub-chain is 1.0 d at ×1 (timeline model) |
| Invention, serialized | ≈10.1 d expected | 4.55 attempts × 53.33 h, one at a time — becomes the critical path if run naively |
| Invention, batched | 2.2 d | 10 attempts in parallel (one per BPC, job-lock), 10 runs + 640 datacores, P(≥1) = 92% |

Batching collapses invention off the critical path entirely — the
batch-size/confidence/datacore trade is the same family as
copy-vs-direct. Two constraints shape it in practice:

- **BPC pool**: 10 BPCs cap a single batch (52 runs total — a shared
  resource that also feeds the hull build's 1 run). More attempts per
  window need copied or purchased BPCs. *(2026-11-20: this pool is
  the recorded example of the copy-destination duality — one BPO's
  copies feeding both invention attempts and manufacturing runs, with
  different consumption semantics; see MILESTONES.md's
  copy-destinations entry.)*
- **Datacores are the real gate**: a 10-attempt batch needs 320 of
  each type; stock is 53 and 11. Acquisition, not scheduling, gates
  the invention branch.

Material determinism: with a **fixed decryptor choice**, ME_eff is
known when the plan is calculated, so T2-component quantities are
deterministic even though the BPC arrives later — parallel is safe.
Deferring the decryptor choice to invention time would shift the bill
with the outcome (≈1% per ME point) — an argument for the
fixed-choice side of the M8 question. Retries append another 53.33 h
window and present as confidence (the M8 expected + confidence
decision), never a deterministic gate.

Scope note: invention here is the **easy case — parallelism of
independent branches**, which waves already handle. It does not
exercise the pipelining question (a consumer starting on partial
deliveries across a dependency edge — see `reference/GLOSSARY.md`);
a real test of that is an edge like the Typhoon chain's AIPS
(Auto-Integrity Preservation Seal) copy queue against phase 4, or this
chain's Fernite Carbide reactions feeding the 18,750-run armor-plate
job (which would have to chunk to pipeline at all).

## Blueprint inventory (live, 2026-11-19)

48 distinct blueprints in the chain — 15 owned, 33 missing.

Missing (the T2 story: invent the ship, buy the components' BPOs):

| Blueprint | Activity |
|---|---|
| R.A.M.- Starship Tech Blueprint | manufacturing |
| Plasma Thruster Blueprint | manufacturing |
| Nanomechanical Microprocessor Blueprint | manufacturing |
| Ladar Sensor Cluster Blueprint | manufacturing |
| Nuclear Reactor Unit Blueprint | manufacturing |
| Deflection Shield Emitter Blueprint | manufacturing |
| Electrolytic Capacitor Unit Blueprint | manufacturing |
| Fernite Carbide Composite Armor Plate Blueprint | manufacturing |
| Capital Jump Drive Blueprint | manufacturing |
| Panther Blueprint | manufacturing |
| Caesarium Cadmide Reaction Formula | reaction |
| Ceramic Powder Reaction Formula | reaction |
| Dysporite Reaction Formula | reaction |
| Fernite Alloy Reaction Formula | reaction |
| Ferrofluid Reaction Formula | reaction |
| Fluxed Condensates Reaction Formula | reaction |
| Hexite Reaction Formula | reaction |
| Hyperflurite Reaction Formula | reaction |
| Neo Mercurite Reaction Formula | reaction |
| Platinum Technite Reaction Formula | reaction |
| Silicon Diborite Reaction Formula | reaction |
| Solerium Reaction Formula | reaction |
| Vanadium Hafnite Reaction Formula | reaction |
| Prometium Reaction Formula | reaction |
| Fernite Carbide Reaction Formula | reaction |
| Sylramic Fibers Reaction Formula | reaction |
| Fullerides Reaction Formula | reaction |
| Phenolic Composites Reaction Formula | reaction |
| Nanotransistors Reaction Formula | reaction |
| Hypersynaptic Fibers Reaction Formula | reaction |
| Ferrogel Reaction Formula | reaction |
| Fermionic Condensates Reaction Formula | reaction |
| Plasmonic Metamaterials Reaction Formula | reaction |

Owned (the T1 Typhoon world carries over intact):

| Blueprint | Copies + originals | Originals |
|---|---:|---:|
| Auto-Integrity Preservation Seal Blueprint | 22 | 2 |
| Carbon Fiber Reaction Formula | 2 | 1 |
| Carbon Polymers Reaction Formula | 2 | 2 |
| Core Temperature Regulator Blueprint | 34 | 1 |
| Helium Fuel Block Blueprint | 2 | 0 |
| Hydrogen Fuel Block Blueprint | 14 | 4 |
| Life Support Backup Unit Blueprint | 28 | 1 |
| Nitrogen Fuel Block Blueprint | 2 | 0 |
| Oxy-Organic Solvents Reaction Formula | 1 | 1 |
| Oxygen Fuel Block Blueprint | 2 | 0 |
| Pressurized Oxidizers Reaction Formula | 2 | 1 |
| Reinforced Carbon Fiber Reaction Formula | 2 | 2 |
| Sulfuric Acid Reaction Formula | 2 | 2 |
| Thermosetting Polymer Reaction Formula | 2 | 1 |
| Typhoon Blueprint | 10 | 0 |

## Mechanics the expansion established

- **Invention is an overlay, not a walk step.** The invented blueprint's
  build inputs resolve through the normal manufacturing walk; the
  invention recipe (source, probability, datacores, skills) reports as
  its own layer. Expected-value quantities (attempts, datacores) stay
  OUT of the deterministic raw-material table — the acquisition table
  stays exact; probabilistic inputs present as expected + confidence
  (the M8 decision).
- **T2 component BPOs are NPC-seeded** (no producer in the SDE). The
  missing-blueprint default (contract BPCs) does not apply to them —
  they're cheap market originals. Blueprint-availability handling
  needs a third acquisition path: invented (the ship), contracted
  (T1 oddments), NPC-market (T2 components).
- **The T1 hull is a build input**: T2 chains nest their T1 chain.
  Phase interleaving follows depth, so the Typhoon's stack and the T2
  layers share phase numbers without sharing nodes.
- **T2 components run at 1 unit/run** with high maxPLs — job counts
  stay low (the armor plates fit one 18,750-run job) but per-run
  material rounding never amortizes: ME on the component BPO is the
  whole cost story, which is why the ME-flavored decryptors matter.
- **Classification gotchas**: Morphite sits in the SDE *Mineral* group
  (it is the top moon material) and Construction Blocks have no
  blueprint at all — both need the name-list fallback alongside the
  molecular-forging tools (category now `npc market goods`).
- **Fuel blocks recur at phases 1–3** again — same shape as the Charon,
  reinforcing the recurring-commodity open question.

## Findings and caveats

- Deepest and widest chain in the set: 7 phases, 1175 tree
  lines, 48 blueprints, 45 raw types.
- The single-inventor bottleneck is structural: only blitzrage holds
  the three invention skills, so ≈10 d of expected invention wall time
  serializes ahead of a 4.2 d ship build. Training a second inventor
  (or using decryptors to cut attempts) is the M13 skill-gap story
  surfacing in the reference model.
- Datacore stock (53 + 11) covers well under one expected success —
  the acquisition table for invention inputs matters as much as the
  mineral totals.
- Invented-BPC base ME/TE (−4/−4 assumed), module base runs, and the
  no-skill-probability-modifier assumption are all **unverified** —
  pin at M8, same standing as the skill→time multipliers.
- No timeline model run for the Panther yet: the invention layer makes
  the scheduler probabilistic (expected attempts ≠ attempts), which is
  M8/M9 design work this document feeds, not something to paper over
  with a deterministic run.
