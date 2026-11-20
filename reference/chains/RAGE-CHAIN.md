# The Scourge Rage heavy assault missile chain — full reference

Sixth chain document (after `TYPHOON-CHAIN.md`, `CHARON-CHAIN.md`,
`PANTHER-CHAIN.md`, `JACKDAW-CHAIN.md`, and `TRIMARK-CHAIN.md`), added
2026-11-20 for the **high-volume consumable** half of the
rigs-and-ammo roadmap step: invention-sourced T2 (Tech 2) ammunition at
production scale (5,000 missiles per run, 100 runs for ×500,000), the
first plan where owned invented-BPC run pool nearly covers the target
(98 of 100 runs), **alternative-product invention** (Javelin siblings
on the same attempt recipe), reaction depth two tiers beneath a
non-ship deliverable, and deterministic over-delivery at the reaction
layer (batch minimums). It is also the first chain since the Typhoon
whose entire skill gate is held live. Every deterministic number here
is output of the reference scripts — regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 2679 500000
```

Provenance: read from the live SDE (Static Data Export) mirror (release
2026-11-13) and the synced live tables (ownership, skills, stock —
2026-11-20). Phases count up in build order (terminators = phase 0,
target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Scourge Rage HAM ×500,000)

- IDs: Scourge Rage Heavy Assault Missile **2679**, Blueprint **2680**
  (maxProductionLimit **10**, 2.67 h/run, **5,000 missiles per run** —
  the first deliverable in the program whose unit count outruns its run
  count by three orders of magnitude). Invented from Scourge Heavy
  Assault Missile Blueprint **26762** (maxProductionLimit 300) at
  **34%**, **10 runs per success** (SDE activity-8 product quantity).
- **Alternative products**: the same attempt recipe also carries the
  Scourge Javelin HAM Blueprint probability row at its own 34% —
  sibling rolls on one recipe, not the T3 grade mechanism and not
  shared-output multi-product. Whether both products can succeed on a
  single attempt, and whether sibling successes count as by-products
  or misses, is **not in the SDE — pin at M8**. Live evidence:
  blitzrage holds 7 Rage BPCs and 0 Javelin BPCs, but 8,595 Javelin
  missiles in inventory — sibling output has happened.
- **The run-pool edge**: ×500,000 needs 100 runs; the owned pool is
  7 BPCs × 14 runs = **98** — a 2-run shortfall, and one invention
  success (10 runs) over-delivers it by 8. E[attempts] for ≥1 Rage
  success = 2.94; n=4 gives 81%, n=7 gives 95%. The plan's invention
  layer is a top-up, not a supply line — the inverse of the Panther,
  where invention was the whole acquisition story.
- **The copy layer is modeled from zero** (2026-11-20 direction, as in
  `TRIMARK-CHAIN.md`): the top-up's 4 attempts consume 4 runs of T1
  BPC — copy 4 × 1-run BPCs from blitzrage's single Scourge HAM BPO
  (4 × 8 min = 32 min, split-invariant) for one parallel invention
  wave. Structurally present but noise on this chain — the copy rate
  (8 min/run vs the Trimark's 60) and the single BPO make the layer a
  sliver either way. From-zero scale reference: 10 successes ≈ a
  35-attempt budget → copy 4.7 h, one 12.67 h invention wave — the
  copy phase still wouldn't own the bar. The owned 586 runs of T1
  copies zero the layer outright.
- **Live-BPC reconciliation (M8 pin evidence)**: the owned BPCs read
  **14 runs, ME 1, TE 8**. Base (SDE quantity 10, **ME 2, TE 4**) plus
  the **Attainment** decryptor (+4 runs, −1 ME, +4 TE) matches all
  three fields exactly. Strong evidence that the invented-BPC base
  ME/TE is **2/4** — the −4/−4 assumed from community docs is stale —
  and that base runs = the SDE activity-8 product quantity. (The
  thirteen owned T2 rig BPCs disagree with their SDE quantity —
  see `TRIMARK-CHAIN.md`'s reconciliation; that half stays open.)
- Materials per run: Rocket Fuel 12, Phenolic Composites 12, Graviton
  Pulse Generator 3, Morphite 1, R.A.M.- Ammunition Tech 1 → ×100
  runs: **1,200 / 1,200 / 300 / 100 / 100**.
- **Reaction depth beneath a non-ship target**: two reaction tiers
  feed the T2 component. Tier 1 (simple): Silicon Diborite, Caesarium
  Cadmide, Vanadium Hafnite, Titanium Chromide, Sulfuric Acid,
  Platinum Technite, Neo Mercurite — R4/R8 moon pairs. Tier 2:
  Phenolic Composites and Nanotransistors (molecular-forged, 3 inputs
  each + a fuel block) and Titanium Carbide (composite, 10,000/run).
  Then Graviton Pulse Generator (manufacturing), then the ammo. Fuel
  blocks thread through as reaction inputs at 5/run — 40 Oxygen,
  15 Nitrogen, 10 Hydrogen, 5 Helium blocks in total, all four types
  already stocked far above need.
- **Deterministic over-delivery at the reaction layer**: batch
  quantities exceed need on 8 of 12 reaction runs — Phenolic 2 ×
  2,200 = 4,400 vs 3,300 needed; Nanotransistors 1,500 vs 600;
  Titanium Carbide 10,000 vs 6,600; Sulfuric Acid / Platinum Technite
  / Neo Mercurite 200 vs 100; Silicon Diborite 400 vs 300; 3 of 4
  fuel-block batches. The reaction analog of invention over-delivery:
  surplus is inventory, or the plan rounds the target up to batch
  size — a target-adjustment surface M6/M9 must own explicitly.
- **Recurring commodity across phases** (cf. the Charon's fuel blocks):
  Phenolic Composites is needed at two depths (1,200 direct to the
  ammo at phase 4, 2,100 into GPGs at phase 3); fuel blocks appear at
  three levels. The merged-campaign question is open — M5/M9.
- Durations: invention 12.67 h/attempt; ammo manufacturing 2.67 h/run
  (a max 10-run job = 26.7 h); GPG 150 s/run (300 runs = 12.5 h, one
  job — maxProductionLimit 4,000); reactions 3 h/run; R.A.M. 42 min;
  T1 copy 8 min/run. Manufacturing owns the slot-hour bar (≈267 h vs
  36 reaction, 38 invention, 12.5 GPG) — but **BPC job-lock owns the
  wall-clock**: 98 owned runs are 7 BPCs, each holding one job at a
  time, so 14 jobs (7 × 10-run + 7 × 4-run) run as two serial rounds,
  26.7 h + 10.7 h. Blueprint count, not slot count, is the
  manufacturing throughput bound.
- Skills: invention Electronic Engineering 1, Rocket Science 1,
  Caldari Encryption Methods 1; ammo manufacturing Graviton Physics 1,
  Rocket Science 1, Industry 5; GPG manufacturing Graviton Physics 3;
  reactions Reactions 2–3. Live check 2026-11-20: **every gate in this
  chain is held** (blitzrage: Caldari Encryption 1, Electronic
  Engineering 1, Rocket Science 1, Graviton Physics 4, Reactions 5,
  Industry 5; four characters at Reactions 5) — the first chain since
  the Typhoon needing no simulation at all.
- Stock highlights: fuel blocks and R4 moon materials fully stocked
  (Oxygen blocks 448 vs 40 needed; Evaporite Deposits 43k vs 300);
  **all R8/R64 moon materials zero** (100–200 each required); Morphite
  6/100; **Rocket Fuel 0/1,200** — no producing blueprint anywhere in
  the SDE, NPC-seeded per community docs (pin against M15 market
  data); datacores Electronic Engineering 29 / Rocket Science 4 vs
  ≈3 + 3 expected for one success. Prior output in inventory: 7,975
  Rage and 8,595 Javelin missiles.

## Per-branch tree (Scourge Rage HAM ×500,000)

```text
- Scourge Rage Heavy Assault Missile x500,000 [manufacturing] (100 runs, 5000/run)
  - Morphite x100  [raw]
  - R.A.M.- Ammunition Tech x100 [manufacturing] (1 runs, 100/run)
    - Tritanium x556  [raw]
    - Pyerite x444  [raw]
    - Mexallon x222  [raw]
    - Isogen x82  [raw]
    - Nocxium x36  [raw]
  - Graviton Pulse Generator x300 [manufacturing] (300 runs, 1/run)
    - Phenolic Composites x2,100 [reaction] (1 runs, 2200/run)
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
    - Nanotransistors x600 [reaction] (1 runs, 1500/run)
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
    - Titanium Carbide x6,600 [reaction] (1 runs, 10000/run)
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
      - Titanium Chromide x100 [reaction] (1 runs, 200/run)
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
        - Titanium x100  [raw]
        - Chromium x100  [raw]
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
  - Rocket Fuel x1,200  [raw]
  - Phenolic Composites x1,200 [reaction] (1 runs, 2200/run)
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
```

## Aggregated phases (shared intermediates merged)

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Scourge Rage Heavy Assault Missile | 500,000 | manufacturing, 100 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Morphite | 100 | raw (terminator) |
| Rocket Fuel | 1,200 | raw (terminator) |
| R.A.M.- Ammunition Tech | 100 | manufacturing, 1 runs |
| Graviton Pulse Generator | 300 | manufacturing, 300 runs |
| Phenolic Composites | 1,200 | reaction, 1 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Tritanium | 556 | raw (terminator) |
| Pyerite | 444 | raw (terminator) |
| Mexallon | 222 | raw (terminator) |
| Isogen | 82 | raw (terminator) |
| Nocxium | 36 | raw (terminator) |
| Oxygen Fuel Block | 5 | manufacturing, 1 runs |
| Silicon Diborite | 100 | reaction, 1 runs |
| Caesarium Cadmide | 100 | reaction, 1 runs |
| Titanium Carbide | 6,600 | reaction, 1 runs |
| Phenolic Composites | 2,100 | reaction, 1 runs |
| Nanotransistors | 600 | reaction, 1 runs |
| Vanadium Hafnite | 100 | reaction, 1 runs |

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 1 | raw (terminator) |
| Enriched Uranium | 4 | raw (terminator) |
| Mechanical Parts | 4 | raw (terminator) |
| Coolant | 9 | raw (terminator) |
| Strontium Clathrates | 20 | raw (terminator) |
| Oxygen | 22 | raw (terminator) |
| Heavy Water | 170 | raw (terminator) |
| Liquid Ozone | 350 | raw (terminator) |
| Oxygen Isotopes | 450 | raw (terminator) |
| Evaporite Deposits | 100 | raw (terminator) |
| Silicates | 100 | raw (terminator) |
| Cadmium | 100 | raw (terminator) |
| Caesium | 100 | raw (terminator) |
| Vanadium | 100 | raw (terminator) |
| Hafnium | 100 | raw (terminator) |
| Nitrogen Fuel Block | 5 | manufacturing, 1 runs |
| Hydrogen Fuel Block | 5 | manufacturing, 1 runs |
| Oxygen Fuel Block | 20 | manufacturing, 1 runs |
| Titanium Chromide | 100 | reaction, 1 runs |
| Silicon Diborite | 200 | reaction, 1 runs |
| Sulfuric Acid | 100 | reaction, 1 runs |
| Platinum Technite | 100 | reaction, 1 runs |
| Caesarium Cadmide | 100 | reaction, 1 runs |
| Neo Mercurite | 100 | reaction, 1 runs |
| Vanadium Hafnite | 100 | reaction, 1 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 3 | raw (terminator) |
| Enriched Uranium | 12 | raw (terminator) |
| Mechanical Parts | 12 | raw (terminator) |
| Coolant | 27 | raw (terminator) |
| Strontium Clathrates | 60 | raw (terminator) |
| Oxygen | 66 | raw (terminator) |
| Heavy Water | 510 | raw (terminator) |
| Liquid Ozone | 1,050 | raw (terminator) |
| Oxygen Isotopes | 450 | raw (terminator) |
| Nitrogen Isotopes | 450 | raw (terminator) |
| Evaporite Deposits | 200 | raw (terminator) |
| Silicates | 100 | raw (terminator) |
| Cadmium | 100 | raw (terminator) |
| Caesium | 100 | raw (terminator) |
| Vanadium | 100 | raw (terminator) |
| Hafnium | 100 | raw (terminator) |
| Atmospheric Gases | 100 | raw (terminator) |
| Platinum | 100 | raw (terminator) |
| Technetium | 100 | raw (terminator) |
| Mercury | 100 | raw (terminator) |
| Neodymium | 100 | raw (terminator) |
| Titanium | 100 | raw (terminator) |
| Chromium | 100 | raw (terminator) |
| Hydrogen Isotopes | 450 | raw (terminator) |
| Nitrogen Fuel Block | 10 | manufacturing, 1 runs |
| Hydrogen Fuel Block | 5 | manufacturing, 1 runs |
| Helium Fuel Block | 5 | manufacturing, 1 runs |
| Oxygen Fuel Block | 15 | manufacturing, 1 runs |

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
| Oxygen Isotopes | 450 | raw (terminator) |
| Hydrogen Isotopes | 450 | raw (terminator) |
| Nitrogen Isotopes | 450 | raw (terminator) |
| Helium Isotopes | 450 | raw (terminator) |

The recurring-commodity pattern is visible in the phase tables:
Phenolic Composites at phases 4 and 3 (1,200 + 2,100 = 3,300 → 2
reaction runs of 2,200), fuel blocks at phases 3–1, Silicon Diborite
at phases 3 and 2 (100 + 200 = 300 → 2 runs of 200), Caesarium Cadmide
and Vanadium Hafnite at phases 3 and 2 (200 each → 1 run each).

## Raw-material acquisition table (Scourge Rage HAM ×500,000)

| Mineral | Required |
|---|---:|
| Tritanium | 556 |
| Pyerite | 444 |
| Mexallon | 222 |
| Isogen | 82 |
| Nocxium | 36 |

| Moon material | Required |
|---|---:|
| Evaporite Deposits | 300 |
| Silicates | 200 |
| Cadmium | 200 |
| Caesium | 200 |
| Hafnium | 200 |
| Vanadium | 200 |
| Atmospheric Gases | 100 |
| Mercury | 100 |
| Titanium | 100 |
| Chromium | 100 |
| Neodymium | 100 |
| Platinum | 100 |
| Technetium | 100 |
| Morphite | 100 |

| PI commodity | Required |
|---|---:|
| Coolant | 72 |
| Enriched Uranium | 32 |
| Mechanical Parts | 32 |
| Robotics | 8 |

| Ice product | Required |
|---|---:|
| Liquid Ozone | 2,800 |
| Heavy Water | 1,360 |
| Oxygen Isotopes | 1,350 |
| Nitrogen Isotopes | 900 |
| Hydrogen Isotopes | 900 |
| Helium Isotopes | 450 |
| Oxygen | 176 |
| Strontium Clathrates | 160 |

| NPC market good | Required |
|---|---:|
| Rocket Fuel | 1,200 |

The PI and ice lines are almost entirely reaction fuel: every fuel
block batch traced in the tree decomposes into them, but the stocked
fuel blocks (448 / 2,398 / 933 / 1,027 across the four isotope types)
cover the plan's 40 / 15 / 10 / 5 requirement directly — the raw tiers
under them only matter if the plan builds blocks instead of drawing
stock. The genuine acquisition story is the R8/R64 moon-material block
(all zero on hand), Morphite (6/100), and Rocket Fuel (0/1,200).

## Invention layer (Scourge Rage Heavy Assault Missile Blueprint)

Source: Scourge Heavy Assault Missile Blueprint (**26762**, activity 8,
invention). Probability **0.34** base (SDE); skill levels are assumed
NOT to modify it post-Crius — pin at M8.

- Materials per attempt: 1 Datacore - Electronic Engineering, 1
  Datacore - Rocket Science (the cheapest attempt in the program —
  against the Panther's 64 datacores). Skills: Electronic Engineering
  1, Rocket Science 1, Caldari Encryption Methods 1.
- T1 consumption: 1 run of the source BPC per attempt (implicit,
  absent from the SDE material list). The from-zero copy layer (key
  facts) sizes 4 one-run BPCs off the single owned BPO for the
  top-up's 4 attempts — the full sizing rule and its wall-clock
  analysis live in `TRIMARK-CHAIN.md`'s Copy layer section; here the
  8 min/run copy rate keeps the phase at 32 minutes regardless of
  split. blitzrage's owned T1 copies (192 + 195 + 199 runs,
  maxProductionLimit 300) make the inventory check trivially green —
  same availability-overlay shape as the Trimark.
- BPC runs per success: **10** (SDE activity-8 product quantity);
  owned BPCs report their ESI-synced 14 (reconciliation below).
- **Alternative products**: Scourge Javelin Heavy Assault Missile
  Blueprint rides the same recipe at its own 0.34. Sibling rolls, not
  the T3 grade mechanism — the planner must decide whether sibling
  successes are by-products (inventory, sellable — the roster already
  holds 8,595 Javelins) or misses; whether both can land on one
  attempt is unpinned. **Pin at M8.**

The plan needs 2 more runs than the 98 owned: **one** Rage success.
E[attempts] = 2.94; P(≥1 Rage success) = 71% at n=3, **81% at n=4**,
87% at n=5, 95% at n=7. Expected datacores per success ≈ 3 + 3 (on
hand: 29 + 4). Each attempt also carries the Javelin roll — at n=4,
E[Javelin successes] ≈ 1.4, i.e. roughly one 10-run Javelin BPC
(50,000 missiles) of by-product per plan.

Decryptor scenarios (modifiers pinned from live ESI dogma 2026-11-19;
base row uses the live-evidence 2/4 base — see reconciliation):

| Decryptor | p_eff | E[attempts]/success | ME_eff | TE | runs |
|---|---:|---:|---:|---:|---:|
| (none) | 0.34 | 2.94 | 2 | 4 | 10 |
| Accelerant | 0.41 | 2.45 | 4 | 14 | 11 |
| Attainment | 0.61 | 1.63 | 1 | 8 | 14 |
| Augmentation | 0.20 | 4.90 | 0 | 6 | 19 |
| Parity | 0.51 | 1.96 | 3 | 2 | 13 |
| Process | 0.37 | 2.67 | 5 | 10 | 10 |
| Symmetry | 0.34 | 2.94 | 3 | 12 | 12 |
| Optimized Attainment | 0.65 | 1.55 | 3 | 2 | 12 |
| Optimized Augmentation | 0.31 | 3.27 | 4 | 4 | 17 |

### Live-BPC reconciliation (M8 pin evidence, 2026-11-20)

The seven owned Rage BPCs uniformly read **14 runs, ME 1, TE 8** from
the live blueprints table. Base (SDE quantity **10** runs, **ME 2,
TE 4**) + **Attainment** (+4 runs, −1 ME, +4 TE) reproduces all three
values exactly — the only decryptor/base combination in the pinned
table that does. Two readings, both pins at M8:

1. **Invented-BPC base ME/TE is 2/4, not −4/−4** — the community-doc
   value the program has assumed (and the script's scenario table
   carries) is stale, most likely pre-Crius. The ammo line's
   three-field match is strong evidence; the Trimark chain's rig BPCs
   (2 runs, ME 0/TE 0) fit no row from either base and stay open
   (`TRIMARK-CHAIN.md`).
2. **The live line ran Attainment decryptors** — probability ×1.8 at
   61% per attempt, which also explains a 7-BPC pool accumulating from
   modest attempt volume.

The planner consequence is the same as the Trimark's: owned BPCs
render synced values; projections use the SDE quantity and a pinned
base, and the base just gained live evidence toward 2/4.

## Blueprint inventory (live, 2026-11-20)

| Blueprint | Activity | Status |
|---|---|---|
| Scourge Rage Heavy Assault Missile Blueprint | invention product | owned — 7 BPCs × 14 runs, ME 1 / TE 8 (98-run pool) |
| Scourge Heavy Assault Missile Blueprint | invention source + T1 build | owned — blitzrage: 1 original (ME 10 / TE 20) + 3 copies (192/195/199 runs) |
| Graviton Pulse Generator Blueprint | manufacturing | **not owned** — NPC-seeded market original (T2 component, as in the Panther chain) |
| R.A.M.- Ammunition Tech Blueprint | manufacturing | not owned — NPC-seeded market original |
| Phenolic Composites Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Nanotransistors Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Silicon Diborite Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Caesarium Cadmide Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Vanadium Hafnite Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Titanium Carbide Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Titanium Chromide Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Sulfuric Acid Reaction Formula | reaction | owned — corporation original |
| Platinum Technite Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Neo Mercurite Reaction Formula | reaction | **not owned** — NPC-seeded original |
| Oxygen / Nitrogen / Hydrogen / Helium Fuel Block Blueprint | manufacturing | owned (corporation + Octavia) — moot while block stock covers need |

Fifteen blueprints, one held in the needed set beyond the invention
pair (Sulfuric Acid, corporation) — the formula gap (9 of 10 reaction
formulas) is this chain's acquisition story, all cheap NPC-seeded
originals per the Panther-chain precedent. The T1 BPO is the live
line's workhorse: its ~586 runs of owned copies make the
invention-input check a formality.

## Mechanics the expansion established

- **Alternative-product invention** is a third dispatch shape: one
  source, multiple probability rows for *different* products (vs. T2's
  single row and T3's one-row-per-grade). The planner semantics —
  sibling successes as by-products or misses, both-on-one-attempt —
  are unpinned and must be a deliberate choice, not an accident of
  the first implementation (M8).
- **Run-pool arithmetic**: plan need (100 runs) vs owned invented-BPC
  runs (98) is a first-class availability meter, distinct from
  blueprint ownership (binary) and material stock (quantities): it
  needs "runs of the right BPC type", summed across copies, compared
  to run-need, with the shortfall routed to the invention layer at a
  confidence target. Over-delivery (10-run successes against a 2-run
  shortfall) lands as spare BPC inventory — **BPC residue** in the
  retry-semantics vocabulary (MILESTONES.md, 2026-11-20): banked for
  future plans, never inflating the current target. This chain is
  the set's over-delivery vehicle; the Trimark set carries the
  under-delivery retry loop.
- **Copy sizing applies here too, but the constants defuse it**: the
  rule (BPC count = min(attempt budget, slot pool); copy time
  split-invariant; copy wall BPO-bound — `TRIMARK-CHAIN.md`'s Copy
  layer section) is chain-general, but this chain's copy rate is
  8 min/run against the Trimark's 60, and its attempt count is 4
  against 35. The same decision that owns the Trimark's timeline is
  a 32-minute sliver here — the planner surfaces the knob, the
  constants decide whether it matters. Destination-wise both new
  chains are pure **Copy → Invention** (T2 BPCs cannot be copied, so
  their manufacturing has no copy option); the dual-destination
  case — one copy wave feeding invention attempts and manufacturing
  runs off the same BPO pool — is the Panther's
  (MILESTONES.md's copy-destinations entry).
- **Volume scales runs, not jobs — until job-lock bites**: the ammo
  BP stacks 10 runs per job (vs. the Trimark rig's hard 1), but the
  owned pool is 7 BPCs, so 14 jobs still queue in two serial rounds
  per blueprint. Throughput bound = min(slots, BPC count ×
  maxProductionLimit); at this scale the BPC count wins.
- **Deterministic over-delivery at reactions**: batch minimums
  (200/run simple, 2,200 molecular-forged, 10,000 composite) exceed
  need on 8 of 12 runs. Surplus-expected quantities belong in the
  same "expected + confidence" presentation the M8 decision gave
  probabilistic inputs — deterministic, but still not "required".
- **Fuel blocks as reaction fuel**: the recurring-commodity question
  (Charon) recurs with a twist — the plan's block need is small
  enough that stock trivially covers it, so the build-vs-stock choice
  collapses the whole ice/PI subtree. The planner's campaign
  aggregation should notice that (skip phase-0/1 block builds when
  stock covers the merged need).
- **A non-ship deliverable stresses different UI surfaces**: the
  target's unit count (500,000) needs thousand separators and
  per-run framing everywhere (5,000/run × 100 runs), and the
  deliverable itself is stackable inventory partially held (7,975
  Rage on hand) — the "delivered" meter counts units, not jobs.

## Findings and caveats

- **The 98/100 edge** is the set piece: the plan is one invention
  success from done, and that success over-delivers 8 spare runs.
  The mockup should show the top-up decision (attempts bought to a
  confidence target) rather than a from-zero invention campaign.
- **Javelin inventory as sibling evidence** (8,595 missiles, 0 BPCs)
  — the by-product question has a live precedent on this very line.
- **Wave shape**: manufacturing owns the bar (≈267 slot-hours of
  100 runs) but runs as two BPC-bound rounds (37.4 h wall-clock);
  reactions are two 3 h tiers; GPG one 12.5 h job; invention one
  12.67 h wave (4 parallel attempts on 1-run copies) alongside a
  32-minute copy sliver, both in parallel with the reaction tiers.
  Serial model total ≈ 2.3 days — a short plan whose interesting
  stress is scheduling shape, not duration.
- **Reaction-formula ownership gap** (1 of 10 needed) — all
  NPC-seeded originals; the acquisition tier for this chain is
  shopping, not copying or inventing.
- **Rocket Fuel** is the second NPC-seeded consumable terminator
  after R.A.M. minerals (R.A.M. itself is buildable here) — verify
  seeding against M15 market data.
- Skills all held live — this chain's set needs no simulation, which
  the mockup README should state plainly (the convention's escape
  hatch exists for the Trimark side, not this one).
- The T1 ammo manufacturing line (Scourge HAM, 100/run from
  minerals) is **not part of this chain**: invention consumes T1 BPC
  runs, not T1 missiles — the same non-nesting the Trimark chain
  established for rigs.
