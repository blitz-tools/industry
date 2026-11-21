# The Typhoon Fleet Issue chain — full reference

Ninth chain document (after `TYPHOON-CHAIN.md` through
`HEL-CHAIN.md`), added 2026-11-21 for the **faction tier** of the
mockup program: the first chain whose target blueprint is acquired
through **loyalty points** — the fifth blueprint acquisition path
(invented · contracted · NPC-seeded · drop-sourced · **LP-earned**),
and the first gated by a *currency* the plan must earn rather than
ISK it can spend anywhere. The build side is the Typhoon's own
world at ×10 scale — deliberately familiar; the acquisition side is
entirely new mechanics. Every deterministic number here is output of
the reference scripts — regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 32311 10
```

Provenance: read from the live SDE (Static Data Export) mirror
(release 2026-11-20) and the synced live tables (ownership, skills,
stock, LP balances — 2026-11-21). Phases count up in build order
(terminators = phase 0, target = highest); math symbols stay
unexpanded — see `reference/GLOSSARY.md`.

## Key facts (Typhoon Fleet Issue ×10)

- IDs: Typhoon Fleet Issue **32311**, Blueprint **32312**
  (maxProductionLimit **10**, 5 h/run, **Industry 1** — the gentlest
  build gate in the program; faction hulls build like T1). No
  producer for the blueprint anywhere in the SDE: the BPC is
  **LP-store only**.
- **The offer table (live, from the fuzzwork lpstore dataset)** —
  the Typhoon Fleet Issue Blueprint sells at the **Tribal Liberation
  Force** (1000182, the Minmatar FW militia corporation), in four
  variants:

  | Offer | LP | ISK | Items | Quantity |
  |---|---:|---:|---|---:|
  | 10-pack | 200,000 | 200,000,000 | 8× Imperial War Reserves Supply Package | 10 BPCs |
  | Single, clean | 100,000 | 20,000,000 | — | 1 |
  | Single, chip | 100,000 | 0 | 2× Minmatar UUC Nexus Chip | 1 |
  | Single, tag | 100,000 | 0 | 1× Hakim Stormare's Tag | 1 |

  Navy stores (Republic Fleet 1000051 and the full Minmatar navy
  corporation set) sell the same BPC at 500,000–600,000 LP — the
  militia store is ~5× cheaper in LP, which makes **FW LP the
  efficient path** and ties this chain to the faction-warfare world
  the corporation already lives in (Amamake is the Minmatar militia
  home). Variant selection is a real planning decision: the 10-pack
  is 20k LP + 20M ISK per BPC against the single's 100k LP — a
  5× LP saving for ISK and an item requirement.
- **Runs per purchased BPC: pin.** The offer dataset carries
  quantity (BPCs per offer) but not each BPC's run count. Assumed
  **1 run per BPC** (the community convention for LP hull copies,
  and the shape maxPL 10 accommodates) — verify in-game at purchase.
  Under that assumption, ×10 ships = ten 1-run BPCs = **ten separate
  5 h manufacturing jobs** (job-lock per BPC) — the Trimark's
  maxPL-1 job shape returning at faction scale, with the BPC count
  set by the offer variant rather than invention dice.
- **The live currency state (2026-11-21, post-re-auth)**: the
  roster's TLF balances are **all zero**, Republic Fleet totals
  8.5k (Storm Ragez 6.5k · theblitzrage 1k · scoopsrage 1k), and
  the corporation's militia LP sits on the corporation itself —
  **in-game-visible, ESI-invisible** (no corporation loyalty route
  exists; probed). The corporation's ~632k LP in Paragon is
  **wrong-currency wealth**: LP does not convert between
  corporations, so it cannot buy this BPC at any price. The
  acquisition plan's front story is the **earn-side lead time**
  (FW plexing at TLF, or the corp-LP distribution workflow)
  against the 200k-LP 10-pack price.
- **Corp LP handling** (the recorded modeling decision): the
  curated manual balance — a structure-manager-style entry per
  corporation, owner-verified against the in-game wallet — plus the
  in-game distribution workflow (directors withdraw corp LP to
  characters; it becomes character LP at the same corporation and
  spends at the same store). The plan renders the curated pool and,
  when it is the source, the distribution step as a plan item.
- **The build is the Typhoon's world at ×10** — deliberately
  familiar: AIPS ×2,000 (667 runs at 3/run — 3 max-run jobs on the
  corp's owned BPOs), LSBU ×1,000 (334 runs), CTR ×10, and the
  mineral bill (Tritanium 80M · Pyerite 40M · Isogen 4M …). All
  three component blueprints are owned; every reaction and fuel
  block formula in the chain is owned. The chain is 6 phases deep —
  the Typhoon's depth exactly.
- Skills: **Industry 1** gates everything (hull and components) —
  the first chain in the program with zero simulated gates and zero
  level-anything requirements beyond Industry 1, held at 5 across
  the entire roster.
- Blueprint inventory: **4 types — 3 owned, 1 LP** (AIPS · LSBU ·
  CTR owned; the TFI Blueprint via the LP store). The smallest
  inventory in the program.

## Per-branch tree (Typhoon Fleet Issue ×10)

```text
- Typhoon Fleet Issue x10 [manufacturing] (10 runs, 1/run)
  - Core Temperature Regulator x10 [manufacturing] (10 runs, 1/run)
    - Chiral Structures x1,000  [raw]
    - Water x1,000  [raw]
    - Pressurized Oxidizers x5,000 [reaction] (25 runs, 200/run)
      - Carbon Polymers x5,000 [reaction] (25 runs, 200/run)
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
        - Hydrocarbons x2,500  [raw]
        - Silicates x2,500  [raw]
      - Sulfuric Acid x5,000 [reaction] (25 runs, 200/run)
        - Nitrogen Fuel Block x125 [manufacturing] (4 runs, 40/run)
          - Robotics x4  [raw]
          - Enriched Uranium x16  [raw]
          - Mechanical Parts x16  [raw]
          - Coolant x36  [raw]
          - Strontium Clathrates x80  [raw]
          - Oxygen x88  [raw]
          - Heavy Water x680  [raw]
          - Liquid Ozone x1,400  [raw]
          - Nitrogen Isotopes x1,800  [raw]
        - Atmospheric Gases x2,500  [raw]
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
  - Life Support Backup Unit x1,000 [manufacturing] (334 runs, 3/run)
    - Test Cultures x2,672  [raw]
    - Viral Agent x2,672  [raw]
    - Reinforced Carbon Fiber x3,340 [reaction] (17 runs, 200/run)
      - Carbon Fiber x3,400 [reaction] (17 runs, 200/run)
        - Hydrogen Fuel Block x85 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Hydrogen Isotopes x1,350  [raw]
        - Hydrocarbons x1,700  [raw]
        - Evaporite Deposits x1,700  [raw]
      - Oxy-Organic Solvents x17 [reaction] (2 runs, 10/run)
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
      - Thermosetting Polymer x3,400 [reaction] (17 runs, 200/run)
        - Oxygen Fuel Block x85 [manufacturing] (3 runs, 40/run)
          - Robotics x3  [raw]
          - Enriched Uranium x12  [raw]
          - Mechanical Parts x12  [raw]
          - Coolant x27  [raw]
          - Strontium Clathrates x60  [raw]
          - Oxygen x66  [raw]
          - Heavy Water x510  [raw]
          - Liquid Ozone x1,050  [raw]
          - Oxygen Isotopes x1,350  [raw]
        - Atmospheric Gases x1,700  [raw]
        - Silicates x1,700  [raw]
  - Auto-Integrity Preservation Seal x2,000 [manufacturing] (667 runs, 3/run)
    - Supertensile Plastics x2,668  [raw]
    - Nanites x2,668  [raw]
    - Reinforced Carbon Fiber x6,670 [reaction] (34 runs, 200/run)
      - Carbon Fiber x6,800 [reaction] (34 runs, 200/run)
        - Hydrogen Fuel Block x170 [manufacturing] (5 runs, 40/run)
          - Robotics x5  [raw]
          - Enriched Uranium x20  [raw]
          - Mechanical Parts x20  [raw]
          - Coolant x45  [raw]
          - Strontium Clathrates x100  [raw]
          - Oxygen x110  [raw]
          - Heavy Water x850  [raw]
          - Liquid Ozone x1,750  [raw]
          - Hydrogen Isotopes x2,250  [raw]
        - Hydrocarbons x3,400  [raw]
        - Evaporite Deposits x3,400  [raw]
      - Oxy-Organic Solvents x34 [reaction] (4 runs, 10/run)
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
      - Thermosetting Polymer x6,800 [reaction] (34 runs, 200/run)
        - Oxygen Fuel Block x170 [manufacturing] (5 runs, 40/run)
          - Robotics x5  [raw]
          - Enriched Uranium x20  [raw]
          - Mechanical Parts x20  [raw]
          - Coolant x45  [raw]
          - Strontium Clathrates x100  [raw]
          - Oxygen x110  [raw]
          - Heavy Water x850  [raw]
          - Liquid Ozone x1,750  [raw]
          - Oxygen Isotopes x2,250  [raw]
        - Atmospheric Gases x3,400  [raw]
        - Silicates x3,400  [raw]
  - Megacyte x40,000  [raw]
  - Zydrine x80,000  [raw]
  - Nocxium x300,000  [raw]
  - Isogen x4,000,000  [raw]
  - Mexallon x6,000,000  [raw]
  - Pyerite x40,000,000  [raw]
  - Tritanium x80,000,000  [raw]
```

## Aggregated phases (shared intermediates merged)

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Typhoon Fleet Issue | 10 | manufacturing, 10 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Megacyte | 40,000 | raw (terminator) |
| Zydrine | 80,000 | raw (terminator) |
| Nocxium | 300,000 | raw (terminator) |
| Isogen | 4,000,000 | raw (terminator) |
| Mexallon | 6,000,000 | raw (terminator) |
| Pyerite | 40,000,000 | raw (terminator) |
| Tritanium | 80,000,000 | raw (terminator) |
| Auto-Integrity Preservation Seal | 2,000 | manufacturing, 667 runs |
| Core Temperature Regulator | 10 | manufacturing, 10 runs |
| Life Support Backup Unit | 1,000 | manufacturing, 334 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Chiral Structures | 1,000 | raw (terminator) |
| Water | 1,000 | raw (terminator) |
| Test Cultures | 2,672 | raw (terminator) |
| Viral Agent | 2,672 | raw (terminator) |
| Supertensile Plastics | 2,668 | raw (terminator) |
| Nanites | 2,668 | raw (terminator) |
| Pressurized Oxidizers | 5,000 | reaction, 25 runs |
| Reinforced Carbon Fiber | 15,010 | reaction, 76 runs |

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Carbon Polymers | 5,000 | reaction, 25 runs |
| Sulfuric Acid | 5,000 | reaction, 25 runs |
| Carbon Fiber | 15,200 | reaction, 76 runs |
| Oxy-Organic Solvents | 101 | reaction, 11 runs |
| Thermosetting Polymer | 15,200 | reaction, 76 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrocarbons | 32,100 | raw (terminator) |
| Silicates | 10,100 | raw (terminator) |
| Atmospheric Gases | 32,100 | raw (terminator) |
| Evaporite Deposits | 10,100 | raw (terminator) |
| Nitrogen Fuel Block | 125 | manufacturing, 4 runs |
| Hydrogen Fuel Block | 380 | manufacturing, 10 runs |
| Helium Fuel Block | 125 | manufacturing, 4 runs |
| Oxygen Fuel Block | 435 | manufacturing, 11 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 29 | raw (terminator) |
| Enriched Uranium | 116 | raw (terminator) |
| Mechanical Parts | 116 | raw (terminator) |
| Coolant | 261 | raw (terminator) |
| Strontium Clathrates | 580 | raw (terminator) |
| Oxygen | 638 | raw (terminator) |
| Heavy Water | 4,930 | raw (terminator) |
| Liquid Ozone | 10,150 | raw (terminator) |
| Helium Isotopes | 1,800 | raw (terminator) |
| Nitrogen Isotopes | 1,800 | raw (terminator) |
| Oxygen Isotopes | 4,950 | raw (terminator) |
| Hydrogen Isotopes | 4,500 | raw (terminator) |

## Raw-material acquisition table (Typhoon Fleet Issue ×10)

| Mineral | Required |
|---|---:|
| Tritanium | 80,000,000 |
| Pyerite | 40,000,000 |
| Mexallon | 6,000,000 |
| Isogen | 4,000,000 |
| Nocxium | 300,000 |
| Zydrine | 80,000 |
| Megacyte | 40,000 |

| Moon material | Required |
|---|---:|
| Hydrocarbons | 32,100 |
| Atmospheric Gases | 32,100 |
| Silicates | 10,100 |
| Evaporite Deposits | 10,100 |

| PI commodity | Required |
|---|---:|
| Test Cultures | 2,672 |
| Viral Agent | 2,672 |
| Supertensile Plastics | 2,668 |
| Nanites | 2,668 |
| Chiral Structures | 1,000 |
| Water | 1,000 |
| Coolant | 261 |
| Enriched Uranium | 116 |
| Mechanical Parts | 116 |
| Robotics | 29 |

| Ice product | Required |
|---|---:|
| Liquid Ozone | 10,150 |
| Oxygen Isotopes | 4,950 |
| Heavy Water | 4,930 |
| Hydrogen Isotopes | 4,500 |
| Helium Isotopes | 1,800 |
| Nitrogen Isotopes | 1,800 |
| Oxygen | 638 |
| Strontium Clathrates | 580 |

Twenty-five raw types — every one already classified, every class
already walked by prior chains. The Typhoon's bill at exactly ×10:
the mineral mountain is the story (80M Tritanium, 40M Pyerite —
against current stock of 97.4M Tritanium **covered** and 652k
Pyerite **1.6%**), with everything else small and familiar.

## Blueprint inventory (live, 2026-11-21)

| Blueprint | Activity | Status |
|---|---|---|
| Typhoon Fleet Issue Blueprint | manufacturing | **not owned — LP store** (TLF militia: 100k–200k LP variants; navy 500–600k) |
| Auto-Integrity Preservation Seal Blueprint | manufacturing | owned — corp BPOs ×2, ME 10 / TE 16 (667 runs = 3 max-run jobs) |
| Life Support Backup Unit Blueprint | manufacturing | owned — corp BPOs ×28 originals + copies |
| Core Temperature Regulator Blueprint | manufacturing | owned — corp BPOs ×34 originals + copies |
| Reaction + fuel-block formulas (7 + 4) | reaction | owned — the Typhoon world intact |

Four blueprint types at the target level — three owned, one
LP-earned — the smallest and most-owned inventory in the program.
The acquisition story is one currency purchase, not shopping.

## Mechanics the expansion established

- **The fifth acquisition path, realized**: LP-earned BPCs are
  currency-gated rather than ISK-gated — the plan's blocking
  resource is a balance at a *specific corporation* (TLF), earned
  through gameplay (FW plexing) or moved by the corp-distribution
  workflow, not bought on any market. The planner needs an
  acquisition node type with: currency balance per corporation
  (character-synced + corp-curated), the offer table (with variant
  selection), and an earn-side lead time that is gameplay, not
  industry.
- **Offer variants are a planning decision**: the same BPC at
  20k LP + 20M ISK (10-pack) vs 100k LP + 20M ISK (single) vs
  100k LP + items — LP-scarce vs ISK-scarce vs item-sourced. The
  planner should present the variant table the way invention sets
  present decryptors: a computed choice with per-variant totals.
- **Militia vs navy pricing (~5×)** makes the store *choice* part
  of the plan: TLF LP and Republic Fleet LP are different
  currencies earning at different rates through different gameplay.
  The wrong-currency rule (no conversion between corporations)
  turns LP wealth into a portfolio question — the M12 capability
  surface's natural extension.
- **The shortfall join is direct**: loyalty balances are keyed by
  `corporation_id`, the same key as the offer catalog's stores —
  offer cost vs held LP is one join once both sync (character LP
  now; the offer catalog via the fuzzwork lpstore dataset, slotted
  as an M15 world-state family).
- **Familiar build, new acquisition**: the material walk is
  byte-for-byte the Typhoon's classes at ×10 — this chain's proof
  is that the acquisition layer composes cleanly on top of a fully
  known build world, exactly the division the planner needs.

## Findings and caveats

- **Runs per LP BPC: pin** (assumed 1 run per BPC — community
  convention; the offer dataset lacks run counts). Under the
  assumption, ×10 is ten 1-run 5 h jobs (job-lock per BPC); if LP
  BPCs carry more runs, the job shape relaxes accordingly.
  Verify at purchase.
- **The earn-side lead time is the plan's front story**: 200k TLF
  LP against zero held — weeks of FW plexing, or the corp-LP
  distribution if the corporation's militia balance covers it
  (curated entry, owner-verified). The mockup set carries this as
  the acquisition front's dead zone.
- **The 10-pack's item requirement** (8× Imperial War Reserves
  Supply Package — an event/tag item) adds an item-sourcing
  sub-step to the cheapest variant; the planner's offer table
  should show requirement availability alongside LP/ISK.
- Pins standing from the investigation: the fuzzwork lpstore
  dataset's coverage (RF ammo BPCs absent from it — verify
  in-game), and the offer catalog's sync cadence (it carries an
  hourly-cached JSON API; treat like other world-state families).
- Skills: none simulated — Industry 1, held at 5 roster-wide; the
  first chain since the Typhoon with a completely green skill
  surface *and* a completely owned build world.
