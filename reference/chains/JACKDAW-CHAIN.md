# The Jackdaw chain — full reference

Fourth chain document (after `TYPHOON-CHAIN.md`, `CHARON-CHAIN.md`, and
`PANTHER-CHAIN.md`), added 2026-11-19 to stress the models with a
**reverse-engineered T3 (Tech 3)** target: relic-based invention (the
relic item itself is the invention "blueprint" — there is no source
blueprint), BPC (Blueprint Copy) runs set by the relic grade instead of
decryptors, two terminator classes no material walk has seen (the
relics and the Sleeper salvage), fullerene polymer reactions that
consume minerals directly, and the first chain where a single invention
success over-delivers the target. Every deterministic number here is
output of the reference scripts — regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 34828 1
```

Provenance: read from the live SDE (Static Data Export) mirror (release
2026-11-13) and the synced live tables (ownership, skills, stock —
2026-11-19). Phases count up in build order (terminators = phase 0,
target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Jackdaw ×1)

- IDs: Jackdaw **34828**, Jackdaw Blueprint **34829**
  (maxProductionLimit 1, 50 h build). Invented from **Sleeper Hull
  Relics** — the relic item itself carries activity 8: Small Intact
  Hull Section **34412** (26%, 20 runs per success), Small
  Malfunctioning **34414** (21%, 10), Small Wrecked **34416** (14%, 3).
  One relic is consumed per attempt — implicit, like the T2 source-BPC
  run, and absent from the SDE material list.
- The recipe is **shared across all four racial tactical destroyers**
  (Confessor, Svipul, Jackdaw, Hecate blueprints are all activity-8
  products of each relic, at the same probability) — the job targets
  one output.
- Skills: Sleeper Encryption Methods 1, Plasma Physics 1, Mechanical
  Engineering 1 — the gentlest gate in the set (the Panther serialized
  on one out-of-corp character at 4/4/1). Live check 2026-11-19:
  **nobody on the roster holds Sleeper Encryption Methods**; blitzrage
  is nearest (both sciences at 4, the encryption skill untrained — it
  needs only level 1). Per the mockup-program convention recorded
  2026-11-19, the Jackdaw set simulates the gate as met; the Panther
  set owns the missing-skills story.
- Attempt time **1 h** (the Panther's is 53.33 h); expected 3.85
  attempts per Intact success.
- Hull inputs: **8 Hybrid Tech Components + R.A.M.- Starship Tech ×10**
  — no T1 hull nested, no racial T2 components. T3 is its own
  production world: fullerene polymer reactions (9 products off
  wormhole fullerites, minerals, and fuel blocks) plus Sleeper salvage.
- **Two new terminator classes**: the invention relics (*Ancient
  Relics* category) and the Sleeper salvage (*Ancient Salvage* group,
  19 types, maps cleanly) — w-space site drops, market-acquired, no
  producing blueprint. The relics enter only through the invention
  overlay; the salvage enters the material walk.
- **Invention over-delivers**: one Intact success yields 20 runs = 20
  Jackdaws' worth of BPC. At ×1 the plan needs one success — buy ≈4
  relics for ~70% confidence, and the surplus runs are inventory.
- Durations: components 10 min/run (maxProductionLimit 1000), polymer
  reactions 3 h/run, Jackdaw build 50 h. **The target build dominates**
  — the inverse of the Charon profile (fast chain, slow deliverable).
- Datacore stock: Plasma Physics 12, Mechanical Engineering 97;
  expected per Intact success ≈ 11.5 of each.

## Per-branch tree (Jackdaw ×1)

Every branch, shared intermediates repeated per parent — 413 lines,
between the Typhoon's 177 and the Charon's 708:

```text
- Jackdaw x1 [manufacturing] (1 runs, 1/run)
  - Electromechanical Interface Nexus x2 [manufacturing] (2 runs, 1/run)
    - PPD Fullerene Fibers x22 [reaction] (1 runs, 250/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x300  [raw]
      - Pyerite x800  [raw]
    - Lanthanum Metallofullerene x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C70 x100  [raw]
      - Fullerite-C84 x100  [raw]
      - Nocxium x200  [raw]
    - Modified Fluid Router x6  [raw]
    - Cartesian Temporal Coordinator x8  [raw]
    - Electromechanical Hull Sheeting x20  [raw]
    - Powdered C-540 Graphite x4  [raw]
    - Graphene Nanoribbons x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C28 x100  [raw]
      - Fullerite-C32 x100  [raw]
      - Nocxium x400  [raw]
  - Fullerene Intercalated Sheets x2 [manufacturing] (2 runs, 1/run)
    - PPD Fullerene Fibers x12 [reaction] (1 runs, 250/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x300  [raw]
      - Pyerite x800  [raw]
    - Fullerene Intercalated Graphite x4 [reaction] (1 runs, 120/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C70 x100  [raw]
      - Mexallon x600  [raw]
    - Powdered C-540 Graphite x8  [raw]
    - Modified Fluid Router x12  [raw]
    - Neurovisual Input Matrix x110  [raw]
    - Melted Nanoribbons x4  [raw]
    - Fulleroferrocene x66 [reaction] (1 runs, 1000/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x200  [raw]
      - Tritanium x1,000  [raw]
  - Fulleroferrocene Power Conduits x2 [manufacturing] (2 runs, 1/run)
    - PPD Fullerene Fibers x22 [reaction] (1 runs, 250/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x300  [raw]
      - Pyerite x800  [raw]
    - Methanofullerene x120 [reaction] (1 runs, 160/run)
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
      - Fullerite-C70 x100  [raw]
      - Fullerite-C72 x100  [raw]
      - Isogen x300  [raw]
    - Powdered C-540 Graphite x6  [raw]
    - Scandium Metallofullerene x88 [reaction] (1 runs, 160/run)
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
      - Zydrine x25  [raw]
      - Fullerite-C72 x100  [raw]
      - Fullerite-C28 x100  [raw]
    - Modified Fluid Router x8  [raw]
    - Neurovisual Input Matrix x8  [raw]
    - Electromechanical Hull Sheeting x12  [raw]
    - Fulleroferrocene x56 [reaction] (1 runs, 1000/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x200  [raw]
      - Tritanium x1,000  [raw]
  - Metallofullerene Plating x8 [manufacturing] (8 runs, 1/run)
    - PPD Fullerene Fibers x32 [reaction] (1 runs, 250/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x300  [raw]
      - Pyerite x800  [raw]
    - Modified Fluid Router x32  [raw]
    - Electromechanical Hull Sheeting x48  [raw]
    - Fulleroferrocene x136 [reaction] (1 runs, 1000/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x200  [raw]
      - Tritanium x1,000  [raw]
  - Optimized Nano-Engines x2 [manufacturing] (2 runs, 1/run)
    - PPD Fullerene Fibers x22 [reaction] (1 runs, 250/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x300  [raw]
      - Pyerite x800  [raw]
    - Fused Nanomechanical Engines x8  [raw]
    - Lanthanum Metallofullerene x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C70 x100  [raw]
      - Fullerite-C84 x100  [raw]
      - Nocxium x200  [raw]
    - Modified Fluid Router x6  [raw]
    - Electromechanical Hull Sheeting x20  [raw]
    - Powdered C-540 Graphite x4  [raw]
    - Graphene Nanoribbons x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C28 x100  [raw]
      - Fullerite-C32 x100  [raw]
      - Nocxium x400  [raw]
  - Reconfigured Subspace Calibrator x2 [manufacturing] (2 runs, 1/run)
    - Lanthanum Metallofullerene x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C70 x100  [raw]
      - Fullerite-C84 x100  [raw]
      - Nocxium x200  [raw]
    - Modified Fluid Router x6  [raw]
    - Electromechanical Hull Sheeting x20  [raw]
    - Graphene Nanoribbons x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C28 x100  [raw]
      - Fullerite-C32 x100  [raw]
      - Nocxium x400  [raw]
    - Resonance Calibration Matrix x8  [raw]
    - Powdered C-540 Graphite x4  [raw]
    - Fulleroferrocene x22 [reaction] (1 runs, 1000/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x200  [raw]
      - Tritanium x1,000  [raw]
  - Self-Assembling Nanolattice x3 [manufacturing] (3 runs, 1/run)
    - C3-FTM Acid x15 [reaction] (1 runs, 100/run)
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
      - Megacyte x80  [raw]
      - Fullerite-C84 x100  [raw]
      - Fullerite-C540 x100  [raw]
    - Carbon-86 Epoxy Resin x39 [reaction] (1 runs, 160/run)
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
      - Zydrine x30  [raw]
      - Fullerite-C32 x100  [raw]
      - Fullerite-C320 x100  [raw]
    - Central System Controller x3  [raw]
    - Defensive Control Node x3  [raw]
    - Emergent Combat Intelligence x3  [raw]
    - Fulleroferrocene x900 [reaction] (1 runs, 1000/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C50 x200  [raw]
      - Tritanium x1,000  [raw]
    - Graphene Nanoribbons x45 [reaction] (1 runs, 120/run)
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
      - Fullerite-C28 x100  [raw]
      - Fullerite-C32 x100  [raw]
      - Nocxium x400  [raw]
    - Heuristic Selfassemblers x6  [raw]
    - Jump Drive Control Nexus x3  [raw]
    - Lanthanum Metallofullerene x120 [reaction] (1 runs, 120/run)
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
      - Fullerite-C70 x100  [raw]
      - Fullerite-C84 x100  [raw]
      - Nocxium x200  [raw]
    - Neurovisual Input Matrix x45  [raw]
    - Thermoelectric Catalysts x3  [raw]
  - Warfare Computation Core x2 [manufacturing] (2 runs, 1/run)
    - Fullerene Intercalated Graphite x22 [reaction] (1 runs, 120/run)
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
      - Fullerite-C60 x100  [raw]
      - Fullerite-C70 x100  [raw]
      - Mexallon x600  [raw]
    - Powdered C-540 Graphite x4  [raw]
    - Scandium Metallofullerene x44 [reaction] (1 runs, 160/run)
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
      - Zydrine x25  [raw]
      - Fullerite-C72 x100  [raw]
      - Fullerite-C28 x100  [raw]
    - Modified Fluid Router x6  [raw]
    - Emergent Combat Analyzer x8  [raw]
    - Electromechanical Hull Sheeting x20  [raw]
    - Graphene Nanoribbons x14 [reaction] (1 runs, 120/run)
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
      - Fullerite-C28 x100  [raw]
      - Fullerite-C32 x100  [raw]
      - Nocxium x400  [raw]
  - R.A.M.- Starship Tech x10 [manufacturing] (1 runs, 100/run)
    - Tritanium x556  [raw]
    - Pyerite x444  [raw]
    - Mexallon x222  [raw]
    - Isogen x82  [raw]
    - Nocxium x36  [raw]
```

## Aggregated phases (shared intermediates merged)

Five phases — shallower than the Charon and Panther (seven each).
Same-type requirements merge per phase, then round runs once.

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Jackdaw | 1 | manufacturing, 1 runs |

### Phase 3

The eight hybrid tech components (all 1/run, maxProductionLimit 1000)
plus R.A.M. (100/run). Job counts stay in single digits — the
component runs equal their required quantities.

| Type | Required | Activity / runs |
|---|---:|---|
| R.A.M.- Starship Tech | 10 | manufacturing, 1 runs |
| Optimized Nano-Engines | 2 | manufacturing, 2 runs |
| Warfare Computation Core | 2 | manufacturing, 2 runs |
| Fullerene Intercalated Sheets | 2 | manufacturing, 2 runs |
| Metallofullerene Plating | 8 | manufacturing, 8 runs |
| Electromechanical Interface Nexus | 2 | manufacturing, 2 runs |
| Fulleroferrocene Power Conduits | 2 | manufacturing, 2 runs |
| Reconfigured Subspace Calibrator | 2 | manufacturing, 2 runs |
| Self-Assembling Nanolattice | 3 | manufacturing, 3 runs |

### Phase 2

The T3 signature phase: Sleeper salvage (15 types) as direct component
inputs, the R.A.M. mineral bill, and the nine polymer reactions. The
salvage types with 3–8 unit requirements are why per-run rounding
never amortizes here — every salvage item lands at exact quantity.

| Type | Required | Activity / runs |
|---|---:|---|
| Modified Fluid Router | 76 | raw (terminator) |
| Cartesian Temporal Coordinator | 8 | raw (terminator) |
| Electromechanical Hull Sheeting | 140 | raw (terminator) |
| Powdered C-540 Graphite | 30 | raw (terminator) |
| Neurovisual Input Matrix | 163 | raw (terminator) |
| Melted Nanoribbons | 4 | raw (terminator) |
| Fused Nanomechanical Engines | 8 | raw (terminator) |
| Resonance Calibration Matrix | 8 | raw (terminator) |
| Central System Controller | 3 | raw (terminator) |
| Defensive Control Node | 3 | raw (terminator) |
| Emergent Combat Intelligence | 3 | raw (terminator) |
| Heuristic Selfassemblers | 6 | raw (terminator) |
| Jump Drive Control Nexus | 3 | raw (terminator) |
| Thermoelectric Catalysts | 3 | raw (terminator) |
| Emergent Combat Analyzer | 8 | raw (terminator) |
| Tritanium | 556 | raw (terminator) |
| Pyerite | 444 | raw (terminator) |
| Mexallon | 222 | raw (terminator) |
| Isogen | 82 | raw (terminator) |
| Nocxium | 36 | raw (terminator) |
| Fulleroferrocene | 1,180 | reaction, 2 runs |
| PPD Fullerene Fibers | 110 | reaction, 1 runs |
| Fullerene Intercalated Graphite | 26 | reaction, 1 runs |
| Methanofullerene | 120 | reaction, 1 runs |
| Lanthanum Metallofullerene | 162 | reaction, 2 runs |
| Scandium Metallofullerene | 132 | reaction, 1 runs |
| Graphene Nanoribbons | 101 | reaction, 1 runs |
| Carbon-86 Epoxy Resin | 39 | reaction, 1 runs |
| C3-FTM Acid | 15 | reaction, 1 runs |

### Phase 1

Reaction inputs: fullerite gases, minerals consumed **directly by
reactions** (a T3 signature — the Typhoon/Charon reactions never touch
minerals), and the four fuel blocks recurring once more.

| Type | Required | Activity / runs |
|---|---:|---|
| Fullerite-C60 | 400 | raw (terminator) |
| Fullerite-C50 | 700 | raw (terminator) |
| Pyerite | 800 | raw (terminator) |
| Fullerite-C70 | 400 | raw (terminator) |
| Fullerite-C84 | 300 | raw (terminator) |
| Nocxium | 800 | raw (terminator) |
| Fullerite-C28 | 200 | raw (terminator) |
| Fullerite-C32 | 200 | raw (terminator) |
| Mexallon | 600 | raw (terminator) |
| Tritanium | 2,000 | raw (terminator) |
| Fullerite-C72 | 200 | raw (terminator) |
| Isogen | 300 | raw (terminator) |
| Zydrine | 55 | raw (terminator) |
| Megacyte | 80 | raw (terminator) |
| Fullerite-C540 | 100 | raw (terminator) |
| Fullerite-C320 | 100 | raw (terminator) |
| Nitrogen Fuel Block | 10 | manufacturing, 1 runs |
| Hydrogen Fuel Block | 15 | manufacturing, 1 runs |
| Helium Fuel Block | 10 | manufacturing, 1 runs |
| Oxygen Fuel Block | 20 | manufacturing, 1 runs |

### Phase 0

Fuel-block inputs — the Typhoon world's PI (Planetary Industry) and
ice stack, unchanged.

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
| Hydrogen Isotopes | 450 | raw (terminator) |
| Oxygen Isotopes | 450 | raw (terminator) |
| Nitrogen Isotopes | 450 | raw (terminator) |
| Helium Isotopes | 450 | raw (terminator) |

## Raw-material acquisition table (Jackdaw ×1)

Chain terminators summed across all stages, grouped by category — 43
raw types. New versus the Panther: the **Sleeper salvage** category (15
types; the SDE *Ancient Salvage* group maps cleanly), and minerals
recurring at phases 1–2 (polymer reactions consume minerals directly;
R.A.M. carries the phase-2 bill). The fullerite gases were already
classified (harvestable clouds). The invention relics and datacores
are invention-layer inputs and live in their own section below —
deliberately kept out of this deterministic table.

### Minerals

| Type | Required |
|---|---:|
| Tritanium | 2,556 |
| Pyerite | 1,244 |
| Nocxium | 836 |
| Mexallon | 822 |
| Isogen | 382 |
| Megacyte | 80 |
| Zydrine | 55 |

### Pi commodities

| Type | Required |
|---|---:|
| Coolant | 36 |
| Enriched Uranium | 16 |
| Mechanical Parts | 16 |
| Robotics | 4 |

### Ice products

| Type | Required |
|---|---:|
| Liquid Ozone | 1,400 |
| Heavy Water | 680 |
| Helium Isotopes | 450 |
| Nitrogen Isotopes | 450 |
| Oxygen Isotopes | 450 |
| Hydrogen Isotopes | 450 |
| Oxygen | 88 |
| Strontium Clathrates | 80 |

### Gas — harvestable clouds

| Type | Required |
|---|---:|
| Fullerite-C50 | 700 |
| Fullerite-C60 | 400 |
| Fullerite-C70 | 400 |
| Fullerite-C84 | 300 |
| Fullerite-C28 | 200 |
| Fullerite-C32 | 200 |
| Fullerite-C72 | 200 |
| Fullerite-C320 | 100 |
| Fullerite-C540 | 100 |

### Sleeper salvage

| Type | Required |
|---|---:|
| Neurovisual Input Matrix | 163 |
| Electromechanical Hull Sheeting | 140 |
| Modified Fluid Router | 76 |
| Powdered C-540 Graphite | 30 |
| Cartesian Temporal Coordinator | 8 |
| Fused Nanomechanical Engines | 8 |
| Resonance Calibration Matrix | 8 |
| Emergent Combat Analyzer | 8 |
| Heuristic Selfassemblers | 6 |
| Melted Nanoribbons | 4 |
| Central System Controller | 3 |
| Defensive Control Node | 3 |
| Emergent Combat Intelligence | 3 |
| Jump Drive Control Nexus | 3 |
| Thermoelectric Catalysts | 3 |

## Invention layer (Jackdaw Blueprint)

The invention overlay — not part of the material walk above. The
Jackdaw Blueprint's *build* inputs resolved normally in the tree; this
is how the blueprint itself is acquired.

- **Source**: the relic item itself carries activity 8 — there is no
  source blueprint. Three grades of Sleeper Hull Relics, same recipe
  across grades: 3× Datacore - Plasma Physics + 3× Datacore -
  Mechanical Engineering per attempt, skills Sleeper Encryption
  Methods 1 / Plasma Physics 1 / Mechanical Engineering 1, 1 h per
  attempt.
- **Runs per success are set by the grade** (the activity-8 product
  quantity in the SDE): Intact 20, Malfunctioning 10, Wrecked 3 — not
  the T2 base-plus-decryptor convention.
- **No decryptors**: T3 reverse engineering has no decryptor slot and
  the invented BPC's ME (Material Efficiency)/TE (Time Efficiency) is
  fixed per grade (community-documented — pin at M8). The T2 decision
  axes (probability vs ME) collapse here.
- **No job-lock**: each attempt consumes its relic — there is no BPC
  pool to serialize on (the Panther's invention was capped at one job
  per source BPC). Concurrency = invention slots × relic stock.
- **Recipe is shared**: each relic's activity-8 products are all four
  racial tactical destroyers at the same probability; the job targets
  one output.

| Grade | p | runs/success | E[attempts] | E[relics] | E[datacores] |
|---|---:|---:|---:|---:|---:|
| Small Intact Hull Section | 0.26 | 20 | 3.85 | 3.85 | 11.5 + 11.5 |
| Small Malfunctioning Hull Section | 0.21 | 10 | 4.76 | 4.76 | 14.3 + 14.3 |
| Small Wrecked Hull Section | 0.14 | 3 | 7.14 | 7.14 | 21.4 + 21.4 |

Confidence for at least one success in n attempts, P = 1 − (1−p)ⁿ:

| Attempts n | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Intact (26%) | 45% | 60% | 70% | 78% | 84% | 88% | 91% |
| Malfunctioning (21%) | 38% | 51% | 61% | 69% | 76% | 81% | 85% |
| Wrecked (14%) | 26% | 36% | 45% | 53% | 60% | 65% | 70% |

### Over-delivery (successes vs runs)

One success satisfies any target up to runs-per-success (20 Intact /
10 Malfunctioning / 3 Wrecked). At ×1 the plan needs exactly one
success — the invention fuel decision is **attempts to buy**
(confidence), not successes needed. Surplus runs are inventory: the
planner's expected-value presentation must handle "1 success, 20
runs, 1 used" without treating the other 19 as waste or as
requirement. This is the first chain where invention over-delivers
the target by an order of magnitude.

### Grade choice (deterministic, pre-pricing)

Per-ship amortized expectations at small targets:

| Grade | E[relics]/ship | E[datacores]/ship | E[wall time]/ship |
|---|---:|---:|---:|
| Small Intact Hull Section | 0.19 | 0.58 + 0.58 | 3.85 h |
| Small Malfunctioning Hull Section | 0.48 | 1.43 + 1.43 | 4.76 h |
| Small Wrecked Hull Section | 2.38 | 7.14 + 7.14 | 7.14 h |

The grade dominates every deterministic axis — per-ship relics,
datacores, and wall time all fall as the grade rises (Wrecked needs
12.5× the relics per ship of Intact). Unlike the T2 decryptor trade
(probability decryptors buy wall time, ME decryptors buy the bill),
there is **no pre-pricing conflict**: use the highest grade the relic
market stocks, and the decision is price-only (M10). This is a
cleaner shape than the Panther's decryptor question and a useful
contrast for the M8 planner design.

### Parallel branch (wave composition)

Invention gates exactly one node — the final ship build — the same
parallel-branch structure as the Panther, but with inverted numbers:
attempts are 1 h (E 3.85 h serialized on one character), so invention
sits trivially off the critical path. The 50 h ship build and the 3 h
reaction runs dominate; the Panther's batching question (10 source
BPCs → one 53.33 h window) cannot arise — there is no BPC pool and no
job-lock, only relic and datacore stock.

Acquisition is the real gate, not scheduling: relic stock is 0 (buy
≈4 Intact for ~70% confidence at ×1), and Plasma Physics datacore
stock (12) covers exactly 4 attempts — Mechanical Engineering (97) is
abundant. The interesting T3 invention question is procurement, the
M10/M15 story, not waves.

### Skills (simulated per program convention)

Live check 2026-11-19: nobody on the roster holds Sleeper Encryption
Methods. blitzrage is nearest (Plasma Physics 4, Mechanical
Engineering 4 — one level-1 skill short); schlepzrage holds Plasma
Physics 3. Per the mockup-program decision of 2026-11-19, the Jackdaw
set simulates the gate as met (blitzrage trained Sleeper Encryption
Methods 1) — the Panther set already covers the missing-skills
scenario, and the remaining sets prioritize chain-system validation.
Recorded here because this document keeps live provenance; the
simulation is a design-program fact, not a live one.

## Blueprint inventory (live, 2026-11-19)

23 distinct blueprints in the chain — **21 owned, 2 missing**. The
most-owned chain in the reference set; the acquisition story is two
items.

Missing:

| Blueprint | Activity | Acquisition |
|---|---|---|
| Jackdaw Blueprint | manufacturing | invented (relic grades above) |
| R.A.M.- Starship Tech Blueprint | manufacturing | NPC-seeded market original (as in the Panther chain) |

Owned — the T3 components as **drop-sourced BPCs** (1000 runs,
ME 10 / TE 20 each — the w-space site-drop signature; no originals on
the roster):

| Blueprint | Copies + originals | Originals |
|---|---:|---:|
| Electromechanical Interface Nexus Blueprint | 2 | 0 |
| Fullerene Intercalated Sheets Blueprint | 2 | 0 |
| Fulleroferrocene Power Conduits Blueprint | 2 | 0 |
| Metallofullerene Plating Blueprint | 2 | 0 |
| Optimized Nano-Engines Blueprint | 2 | 0 |
| Reconfigured Subspace Calibrator Blueprint | 2 | 0 |
| Self-Assembling Nanolattice Blueprint | 3 | 0 |
| Warfare Computation Core Blueprint | 1 | 0 |

Owned — the Typhoon world carries over (fuel blocks and every polymer
formula as originals):

| Blueprint | Copies + originals | Originals |
|---|---:|---:|
| Hydrogen Fuel Block Blueprint | 14 | 4 |
| Helium Fuel Block Blueprint | 2 | 0 |
| Nitrogen Fuel Block Blueprint | 2 | 0 |
| Oxygen Fuel Block Blueprint | 2 | 0 |
| Fulleroferrocene Reaction Formula | 1 | 1 |
| PPD Fullerene Fibers Reaction Formula | 1 | 1 |
| Fullerene Intercalated Graphite Reaction Formula | 1 | 1 |
| Methanofullerene Reaction Formula | 1 | 1 |
| Lanthanum Metallofullerene Reaction Formula | 1 | 1 |
| Scandium Metallofullerene Reaction Formula | 1 | 1 |
| Graphene Nanoribbons Reaction Formula | 1 | 1 |
| Carbon-86 Epoxy Resin Reaction Formula | 1 | 1 |
| C3-FTM Acid Reaction Formula | 1 | 1 |

**Drop-sourced BPCs are a fourth acquisition path**: the hybrid tech
component blueprints have no producer, no invention recipe, and (per
community documentation) no NPC market seeding — the 1000-run ME 10 /
TE 20 copies are w-space relic/data site drops, acquired by farming
or buying resold copies. The planner's blueprint-availability handling
needs this path alongside invented / contracted / NPC-seeded; verify
the no-market-seeding claim when M15's market data lands.

## Mechanics the expansion established

- **T3 reverse engineering in the SDE**: the relic item itself carries
  activity 8 — there is no source blueprint to walk. Probability rows
  come one per relic grade; BPC runs per success are the activity-8
  product quantity (20/10/3). The T2 conventions (runs = base +
  decryptor modifier, base ME/TE −4/−4) do not apply — ME/TE is fixed
  per grade; pin the values at M8.
- **Multi-product invention recipes**: each relic's recipe lists every
  product of its grade family (all four racial tactical destroyers)
  at the same probability; the job targets one output at install. The
  resolver must read probability per (source, product) pair, not
  assume one product per recipe — the T2 overlay's take-the-first
  row is only safe because T2 recipes are single-product.
- **No job-lock on relic invention**: each attempt consumes its relic,
  so concurrency is slots × relic stock — versus the T2 cap of one
  job per source BPC.
- **Two new terminator classes**: the relics (*Ancient Relics*
  category) and the Sleeper salvage (*Ancient Salvage* group, 19
  types — maps cleanly, no fallback needed). Both are w-space drops;
  only the salvage enters the material walk.
- **Invention over-delivery**: successes needed =
  ⌈target ÷ runs-per-success⌉; at small targets one success
  over-satisfies and the surplus is inventory. Expected-value inputs
  stay out of the deterministic raw table — the Panther's rule,
  unchanged.
- **Reactions with mineral inputs**: the polymer reactions consume
  minerals and fuel blocks directly, so minerals recur at phases 1–2
  (R.A.M. carries the phase-2 bill) — the recurring-commodity
  question widens beyond fuel blocks.
- **Fourth blueprint acquisition path**: drop-sourced BPCs —
  component copies from w-space sites, finite-run but effectively
  unconstrained at these volumes (1000 runs against 2–8 needed).

## Findings and caveats

- A mid-sized chain by tree width (413 lines) but structurally the
  simplest acquisition story yet: 5 phases, 23 blueprints (21 owned),
  43 raw types plus 3 invention inputs (relic grade + 2 datacores).
  Two items to acquire: invent the ship, buy a R.A.M. BPO.
- **No copy plan at all**: components sit on 1000-run BPCs and every
  formula is an original — copying never appears in this chain. The
  planner's copy-strategy section must render as absent on such
  chains, not as an error or an empty queue (edge case for M9's
  surface).
- The **50 h ship build dominates** wall time — the inverse-Charon:
  everything below the target is fast (10-minute components, 3-hour
  reactions, 1-hour invention attempts). Expect few waves with a long
  final one; the wave bar's dead zones will live *between* waves,
  not inside them.
- Invention is off the critical path by construction; the interesting
  T3 question is relic procurement (E 3.85 Intact relics, stock 0),
  and the datacore asymmetry (Plasma Physics 12 = exactly 4 attempts;
  Mechanical Engineering 97 = 32 attempts) — an acquisition-table
  story, not a scheduling one.
- Tactical destroyers have no subsystems (modes, not slots). The
  earlier "hull + subsystems planned together" idea was corrected
  2026-11-19: subsystems (strategic cruisers) are independent
  products that no hull consumes — multi-target planning, if ever
  wanted, is a target-set UI feature, not a chain mechanic.
- Unverified pins: T3 invented-BPC ME/TE values per grade, decryptor
  non-applicability, any skill effect on probability — pin at M8,
  same standing as the T2 pins. Relic/salvage market sourcing is
  community-documented; verify against M15 market data.
