# The Charon chain — full reference

Second chain document (after `TYPHOON-CHAIN.md`), added 2026-11-18 to
stress the models with a **capital** target: capital components, PI
tier-4 inputs, gas reactions, advanced moon reactions, a seven-deep
phase stack, and recurring commodities. Every number here is
deterministic output of the reference scripts — regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 20185 1
podman exec industry_dev_1 python reference/timeline_model.py 20185 1
podman exec industry_dev_1 python reference/timeline_model.py 20185 1 \
    --timelines 1,2,5
```

Provenance: read directly from the live SDE (Static Data Export) mirror
(release 2026-11-13), the same source as `TYPHOON-CHAIN.md`. Phases
count up in build order (terminators = phase 0, target = highest);
math symbols stay unexpanded — see `reference/GLOSSARY.md`.

## Per-branch tree (Charon ×1)

Every branch, shared intermediates repeated per parent — 708 lines,
the widest chain in the reference set:

```text
- Charon x1 [manufacturing] (1 runs, 1/run)
  - Capital Propulsion Engine x5 [manufacturing] (5 runs, 1/run)
    - Self-Harmonizing Power Core x5  [raw]
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
    - Megacyte x1,425  [raw]
    - Zydrine x2,850  [raw]
    - Nocxium x5,625  [raw]
    - Isogen x56,250  [raw]
    - Tritanium x202,500  [raw]
    - Mexallon x202,500  [raw]
    - Pyerite x731,250  [raw]
  - Capital Armor Plates x5 [manufacturing] (5 runs, 1/run)
    - Organic Mortar Applicators x25  [raw]
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
    - Megacyte x1,540  [raw]
    - Zydrine x3,075  [raw]
    - Nocxium x6,000  [raw]
    - Isogen x60,000  [raw]
    - Tritanium x225,000  [raw]
    - Mexallon x225,000  [raw]
    - Pyerite x787,500  [raw]
  - Capital Cargo Bay x50 [manufacturing] (50 runs, 1/run)
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
    - Megacyte x19,000  [raw]
    - Zydrine x38,000  [raw]
    - Nocxium x75,000  [raw]
    - Isogen x750,000  [raw]
    - Tritanium x2,700,000  [raw]
    - Mexallon x2,700,000  [raw]
    - Pyerite x9,750,000  [raw]
  - Capital Construction Parts x5 [manufacturing] (5 runs, 1/run)
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
    - Megacyte x1,050  [raw]
    - Zydrine x2,065  [raw]
    - Nocxium x3,750  [raw]
    - Isogen x45,000  [raw]
    - Tritanium x150,000  [raw]
    - Mexallon x150,000  [raw]
    - Pyerite x525,000  [raw]
  - R-O Trigger Neurolink Conduit x16 [manufacturing] (16 runs, 1/run)
    - Pressurized Oxidizers x160 [reaction] (1 runs, 200/run)
      - Carbon Polymers x200 [reaction] (1 runs, 200/run)
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
        - Hydrocarbons x100  [raw]
        - Silicates x100  [raw]
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
      - Oxy-Organic Solvents x1 [reaction] (1 runs, 10/run)
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
    - Reinforced Carbon Fiber x160 [reaction] (1 runs, 200/run)
      - Carbon Fiber x200 [reaction] (1 runs, 200/run)
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
        - Hydrocarbons x100  [raw]
        - Evaporite Deposits x100  [raw]
      - Oxy-Organic Solvents x1 [reaction] (1 runs, 10/run)
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
      - Thermosetting Polymer x200 [reaction] (1 runs, 200/run)
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
        - Atmospheric Gases x100  [raw]
        - Silicates x100  [raw]
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
    - Reaction-Orienting Neurolink Stabilizer x16 [reaction] (2 runs, 10/run)
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
      - Amber Cytoserocin x20  [raw]
      - Golden Cytoserocin x20  [raw]
      - AG-Composite Molecular Condenser x2  [raw]
  - Gravimetric-FTL Interlink Communicator x1 [manufacturing] (1 runs, 1/run)
    - Self-Harmonizing Power Core x1  [raw]
    - Wetware Mainframe x1  [raw]
    - Broadcast Node x2  [raw]
    - Fermionic Condensates x40 [reaction] (1 runs, 200/run)
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
      - Dysporite x100 [reaction] (1 runs, 200/run)
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
        - Dysprosium x100  [raw]
      - Fluxed Condensates x100 [reaction] (1 runs, 200/run)
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
        - Neodymium x100  [raw]
        - Thulium x100  [raw]
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
    - Scandium Metallofullerene x130 [reaction] (1 runs, 160/run)
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
    - PPD Fullerene Fibers x190 [reaction] (1 runs, 250/run)
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
    - Methanofullerene x190 [reaction] (2 runs, 160/run)
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
      - Fullerite-C70 x200  [raw]
      - Fullerite-C72 x200  [raw]
      - Isogen x600  [raw]
    - Lanthanum Metallofullerene x190 [reaction] (2 runs, 120/run)
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
      - Fullerite-C70 x200  [raw]
      - Fullerite-C84 x200  [raw]
      - Nocxium x400  [raw]
    - C3-FTM Acid x260 [reaction] (3 runs, 100/run)
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
      - Megacyte x240  [raw]
      - Fullerite-C84 x300  [raw]
      - Fullerite-C540 x300  [raw]
    - Carbon-86 Epoxy Resin x380 [reaction] (3 runs, 160/run)
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
      - Zydrine x90  [raw]
      - Fullerite-C32 x300  [raw]
      - Fullerite-C320 x300  [raw]
    - Fullerene Intercalated Graphite x390 [reaction] (4 runs, 120/run)
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
      - Fullerite-C60 x400  [raw]
      - Fullerite-C70 x400  [raw]
      - Mexallon x2,400  [raw]
    - Graphene Nanoribbons x560 [reaction] (5 runs, 120/run)
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
      - Fullerite-C28 x500  [raw]
      - Fullerite-C32 x500  [raw]
      - Nocxium x2,000  [raw]
    - Nonlinear Metamaterials x560 [reaction] (2 runs, 300/run)
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
      - Titanium Chromide x200 [reaction] (1 runs, 200/run)
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
      - Ferrofluid x200 [reaction] (1 runs, 200/run)
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
    - Fulleroferrocene x660 [reaction] (1 runs, 1000/run)
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
  - Auto-Integrity Preservation Seal x400 [manufacturing] (134 runs, 3/run)
    - Supertensile Plastics x536  [raw]
    - Nanites x536  [raw]
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
  - Life Support Backup Unit x200 [manufacturing] (67 runs, 3/run)
    - Test Cultures x536  [raw]
    - Viral Agent x536  [raw]
    - Reinforced Carbon Fiber x670 [reaction] (4 runs, 200/run)
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
  - Capital Core Temperature Regulator x1 [manufacturing] (1 runs, 1/run)
    - Integrity Response Drones x20  [raw]
    - Self-Harmonizing Power Core x20  [raw]
    - Core Temperature Regulator x35 [manufacturing] (35 runs, 1/run)
      - Chiral Structures x3,500  [raw]
      - Water x3,500  [raw]
      - Pressurized Oxidizers x17,500 [reaction] (88 runs, 200/run)
        - Carbon Polymers x17,600 [reaction] (88 runs, 200/run)
          - Helium Fuel Block x440 [manufacturing] (11 runs, 40/run)
            - Robotics x11  [raw]
            - Enriched Uranium x44  [raw]
            - Mechanical Parts x44  [raw]
            - Coolant x99  [raw]
            - Strontium Clathrates x220  [raw]
            - Oxygen x242  [raw]
            - Heavy Water x1,870  [raw]
            - Liquid Ozone x3,850  [raw]
            - Helium Isotopes x4,950  [raw]
          - Hydrocarbons x8,800  [raw]
          - Silicates x8,800  [raw]
        - Sulfuric Acid x17,600 [reaction] (88 runs, 200/run)
          - Nitrogen Fuel Block x440 [manufacturing] (11 runs, 40/run)
            - Robotics x11  [raw]
            - Enriched Uranium x44  [raw]
            - Mechanical Parts x44  [raw]
            - Coolant x99  [raw]
            - Strontium Clathrates x220  [raw]
            - Oxygen x242  [raw]
            - Heavy Water x1,870  [raw]
            - Liquid Ozone x3,850  [raw]
            - Nitrogen Isotopes x4,950  [raw]
          - Atmospheric Gases x8,800  [raw]
          - Evaporite Deposits x8,800  [raw]
        - Oxy-Organic Solvents x88 [reaction] (9 runs, 10/run)
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
          - Hydrocarbons x18,000  [raw]
          - Atmospheric Gases x18,000  [raw]
      - Reinforced Carbon Fiber x17,500 [reaction] (88 runs, 200/run)
        - Carbon Fiber x17,600 [reaction] (88 runs, 200/run)
          - Hydrogen Fuel Block x440 [manufacturing] (11 runs, 40/run)
            - Robotics x11  [raw]
            - Enriched Uranium x44  [raw]
            - Mechanical Parts x44  [raw]
            - Coolant x99  [raw]
            - Strontium Clathrates x220  [raw]
            - Oxygen x242  [raw]
            - Heavy Water x1,870  [raw]
            - Liquid Ozone x3,850  [raw]
            - Hydrogen Isotopes x4,950  [raw]
          - Hydrocarbons x8,800  [raw]
          - Evaporite Deposits x8,800  [raw]
        - Oxy-Organic Solvents x88 [reaction] (9 runs, 10/run)
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
          - Hydrocarbons x18,000  [raw]
          - Atmospheric Gases x18,000  [raw]
        - Thermosetting Polymer x17,600 [reaction] (88 runs, 200/run)
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
          - Atmospheric Gases x8,800  [raw]
          - Silicates x8,800  [raw]
```

## Aggregated phases (shared intermediates merged)

Same-type requirements merge per phase, then round runs once. **New
shape vs the Typhoon: the same commodity recurs across phases** —
fuel blocks at phases 1, 2, and 3; PO (Pressurized Oxidizers) and RCF
(Reinforced Carbon Fiber) at phases 3 and 4; Carbon Fiber and the
other R4 reaction intermediates at phases 2 and 3 — because their
consumers sit at different depths. Aggregation merges within a phase,
never across phases (see Mechanics).

| Phase | Node | Qty | Activity | Runs |
|---|---|---|---|---|
| 6 | Charon | 1 | manufacturing | 1 |
| 5 | Capital Propulsion Engine | 5 | manufacturing | 5 |
| 5 | Capital Armor Plates | 5 | manufacturing | 5 |
| 5 | Capital Cargo Bay | 50 | manufacturing | 50 |
| 5 | Capital Construction Parts | 5 | manufacturing | 5 |
| 5 | R-O Trigger Neurolink Conduit | 16 | manufacturing | 16 |
| 5 | Gravimetric-FTL Interlink Communicator | 1 | manufacturing | 1 |
| 5 | Auto-Integrity Preservation Seal | 400 | manufacturing | 134 |
| 5 | Life Support Backup Unit | 200 | manufacturing | 67 |
| 5 | Capital Core Temperature Regulator | 1 | manufacturing | 1 |
| 4 | Fermionic Condensates | 40 | reaction | 1 |
| 4 | Fulleroferrocene | 660 | reaction | 1 |
| 4 | PPD Fullerene Fibers | 190 | reaction | 1 |
| 4 | Fullerene Intercalated Graphite | 390 | reaction | 4 |
| 4 | Methanofullerene | 190 | reaction | 2 |
| 4 | Lanthanum Metallofullerene | 190 | reaction | 2 |
| 4 | Scandium Metallofullerene | 130 | reaction | 1 |
| 4 | Graphene Nanoribbons | 560 | reaction | 5 |
| 4 | Carbon-86 Epoxy Resin | 380 | reaction | 3 |
| 4 | C3-FTM Acid | 260 | reaction | 3 |
| 4 | Nonlinear Metamaterials | 560 | reaction | 2 |
| 4 | Pressurized Oxidizers | 160 | reaction | 1 |
| 4 | Reinforced Carbon Fiber | 8,670 | reaction | 44 |
| 4 | Axosomatic Neurolink Enhancer | 640 | reaction | 32 |
| 4 | Reaction-Orienting Neurolink Stabilizer | 16 | reaction | 2 |
| 4 | Core Temperature Regulator | 35 | manufacturing | 35 |
| 3 | Nitrogen Fuel Block | 220 | manufacturing | 6 |
| 3 | Hydrogen Fuel Block | 35 | manufacturing | 1 |
| 3 | Helium Fuel Block | 25 | manufacturing | 1 |
| 3 | Oxygen Fuel Block | 15 | manufacturing | 1 |
| 3 | Titanium Chromide | 200 | reaction | 1 |
| 3 | Carbon Polymers | 200 | reaction | 1 |
| 3 | Sulfuric Acid | 200 | reaction | 1 |
| 3 | Caesarium Cadmide | 100 | reaction | 1 |
| 3 | Dysporite | 100 | reaction | 1 |
| 3 | Ferrofluid | 200 | reaction | 1 |
| 3 | Fluxed Condensates | 100 | reaction | 1 |
| 3 | Prometium | 100 | reaction | 1 |
| 3 | Carbon Fiber | 8,800 | reaction | 44 |
| 3 | Oxy-Organic Solvents | 45 | reaction | 5 |
| 3 | Thermosetting Polymer | 8,800 | reaction | 44 |
| 3 | Pressurized Oxidizers | 17,500 | reaction | 88 |
| 3 | Reinforced Carbon Fiber | 17,500 | reaction | 88 |
| 2 | Nitrogen Fuel Block | 5 | manufacturing | 1 |
| 2 | Hydrogen Fuel Block | 225 | manufacturing | 6 |
| 2 | Helium Fuel Block | 10 | manufacturing | 1 |
| 2 | Oxygen Fuel Block | 265 | manufacturing | 7 |
| 2 | Carbon Polymers | 17,600 | reaction | 88 |
| 2 | Sulfuric Acid | 17,600 | reaction | 88 |
| 2 | Carbon Fiber | 17,600 | reaction | 88 |
| 2 | Oxy-Organic Solvents | 176 | reaction | 18 |
| 2 | Thermosetting Polymer | 17,600 | reaction | 88 |
| 1 | Nitrogen Fuel Block | 440 | manufacturing | 11 |
| 1 | Hydrogen Fuel Block | 440 | manufacturing | 11 |
| 1 | Helium Fuel Block | 440 | manufacturing | 11 |
| 1 | Oxygen Fuel Block | 530 | manufacturing | 14 |

## Raw-material acquisition table (Charon ×1)

All terminators summed across the whole chain. **Four terminator
classes the Typhoon chain never exercised** appear here: advanced
moon materials (R8–R64), gas from harvestable clouds (wormhole
fullerites and k-space mykoserocins/cytoserocins), PI tier-4
commodities (capital-component inputs), and molecular-forging tools.

**minerals**

| Type | Qty |
|---|---|
| Pyerite | 11,794,550 |
| Mexallon | 3,279,900 |
| Tritanium | 3,278,500 |
| Isogen | 911,850 |
| Nocxium | 92,775 |
| Zydrine | 46,105 |
| Megacyte | 23,255 |

**moon materials**

| Type | Qty |
|---|---|
| Hydrocarbons | 68,100 |
| Atmospheric Gases | 68,100 |
| Silicates | 22,100 |
| Evaporite Deposits | 22,100 |
| Cadmium | 200 |
| Dysprosium | 200 |
| Caesium | 100 |
| Mercury | 100 |
| Titanium | 100 |
| Chromium | 100 |
| Hafnium | 100 |
| Neodymium | 100 |
| Promethium | 100 |
| Thulium | 100 |

**PI commodities**

| Type | Qty |
|---|---|
| Chiral Structures | 3,500 |
| Water | 3,500 |
| Coolant | 639 |
| Test Cultures | 536 |
| Viral Agent | 536 |
| Supertensile Plastics | 536 |
| Nanites | 536 |
| Enriched Uranium | 284 |
| Mechanical Parts | 284 |
| Robotics | 71 |
| Self-Harmonizing Power Core | 26 |
| Organic Mortar Applicators | 25 |
| Integrity Response Drones | 20 |
| Broadcast Node | 2 |
| Wetware Mainframe | 1 |

**ice products**

| Type | Qty |
|---|---|
| Liquid Ozone | 24,850 |
| Heavy Water | 12,070 |
| Oxygen Isotopes | 9,900 |
| Nitrogen Isotopes | 8,100 |
| Hydrogen Isotopes | 8,100 |
| Helium Isotopes | 5,850 |
| Oxygen | 1,562 |
| Strontium Clathrates | 1,420 |

**gas (harvestable clouds)**

| Type | Qty |
|---|---|
| Amber Mykoserocin | 1,280 |
| Golden Mykoserocin | 1,280 |
| Fullerite-C32 | 800 |
| Fullerite-C70 | 800 |
| Fullerite-C28 | 600 |
| Fullerite-C60 | 600 |
| Fullerite-C50 | 500 |
| Fullerite-C84 | 500 |
| Fullerite-C72 | 300 |
| Fullerite-C320 | 300 |
| Fullerite-C540 | 300 |
| Amber Cytoserocin | 20 |
| Golden Cytoserocin | 20 |

**molecular-forging tools**

| Type | Qty |
|---|---|
| AG-Composite Molecular Condenser | 34 |

## Mechanics the expansion established

- **The SDE's own grouping classifies almost every terminator** —
  `invGroups` 'Moon Materials', 'Harvestable Cloud', and the
  Planetary Commodities groups map 1:1 to the categories M5 needs.
  The single exception: molecular-forging tools sit in the generic
  'Commodities' catch-all group (alongside skill-point items), so M5
  needs a small name-list fallback for them.
- **Recurring commodities across phases are real, not an artifact.**
  Fuel blocks, PO, RCF, Carbon Fiber, and the other R4 intermediates
  appear in multiple phases because different consumers need them at
  different depths. Two readings: build one merged campaign at the
  earliest need (simplest, ties up inputs early), or per-phase
  campaigns (pipelining-adjacent). Open question for M5/M9 — the
  reference model currently builds them per phase, which is why the
  copy pipeline lists fuel-block sets three times.
- **Mixed-activity phases**: the Typhoon's phases were pure (all
  manufacturing or all reaction); the Charon's phases 2–4 each mix
  manufacturing and reaction items. The scheduling model's
  reaction branch only triggers for all-reaction phases, so mixed
  phases schedule through the slot-hour formula — an approximation
  flagged in Findings below.
- **Capital component shapes**: PI tier-4 inputs (Wetware Mainframe,
  Broadcast Node, Self-Harmonizing Power Core, Organic Mortar
  Applicators, Integrity Response Drones), gas inputs (the neurolink
  conduits consume mykoserocins), and fullerite reactions (T2-style
  advanced reactions, activity 11 like any other) — all resolve
  through the same generic activity machinery with no special cases.
- **`maxProductionLimit` (Charon blueprint) = 1** — every Charon BPC
  (Blueprint Copy) is a single run; a ×N plan means N sequential
  single-run copies from the one BPO (Blueprint Original), which is
  what makes the ship's own copy pipeline the chain's critical path.

## Time-balanced model (Charon ×1)

Pool: 3 characters × 10 slots (live roster, max-skills scenario
multiplier 0.680 — all three currently compute 0.680). Job shape per
phase (condensed; full output from the regen command above):

| Phase | Activity | Duration | Job shape |
|---|---|---|---|
| 6 — Charon | mfg | 283.3h = 48 windows | 1 BPC × 1 run |
| 5 — capital + regular components | mfg | 0.4d | Cargo Bay 25 BPCs ×2; AIPS (Auto-Integrity Preservation Seal) 27 BPCs ×≈5; LSBU (Life Support Backup Unit) 23 BPCs ×≈3; CTR (Core Temperature Regulator) 18 BPCs ×2; capital parts 5 BPCs ×1 each |
| 4 — advanced reactions + CTR | mixed | 1.9d | RCF 44 runs (3 BPO jobs), neurolink enhancer 32 runs (3 BPO jobs), fullerite reactions 1–4 runs each, CTR 35 runs (18 BPCs ×2) |
| 3 — R4 reactions + fuel blocks | mixed | 3.7d | CP/SA/CF/TP 44 runs each (3 BPO jobs), PO/RCF 88 runs each, fuel blocks 1–6 runs |
| 2 — R4 reactions + fuel blocks | mixed | 3.8d | CP/SA/CF/TP/OOS 88/18 runs (3 BPO jobs), fuel blocks 1–11 runs |
| 1 — fuel blocks | mfg | ≈0 | 440–530 units, 11–14 runs |

Copy pipeline (parallel across types, sequential per BPO): the
**Charon BPC dominates at 13.9 d**; everything else fits inside it —
Capital Cargo Bay 7.4 d, CTR 2.6 d, AIPS 2.2 d, LSBU 1.1 d, capital
parts ≤ 0.7 d, fuel blocks ≤ 0.1 d.

## Timelines (pure-copy strategy)

```text
CHARON x1 — end 25.7d (25.69 d/unit)
  phase 1 mfg                            0.1 ->    0.1d
  phase 2 mfg                            0.1 ->    3.9d
  phase 3 mfg                            3.9 ->    7.6d
  phase 4 mfg                            7.6 ->    9.5d
  phase 5 mfg                            9.5 ->    9.9d
  BUILDS WAIT                            9.9 ->   13.9d   <- Charon copy
  phase 6 mfg                           13.9 ->   25.7d

CHARON x2 — end 39.6d (19.79 d/unit)
  phases 1-5                             0.2 ->   19.5d
  BUILDS WAIT                           19.5 ->   27.8d   <- Charon copy
  phase 6 mfg                           27.8 ->   39.6d

CHARON x5 — end 81.2d (16.25 d/unit)
  phases 1-5                             0.6 ->   48.3d
  BUILDS WAIT                           48.3 ->   69.4d   <- Charon copy
  phase 6 mfg                           69.4 ->   81.2d
```

The Charon's own copy queue is the critical path at every N — ≈13.9 d
per ship, linear, because each copy is a single-run BPC off one BPO.
The reaction phases scale with N and eventually dominate the input
side, but the copy dead wait grows just as fast.

## Strategy comparison (copy vs hybrid)

The hybrid rule (copy until inputs arrive, then build direct —
see `reference/GLOSSARY.md`) applies cleanly to the Charon because
its skilled build time per run (8.0 d) beats its copy time per run
(13.9 d):

| N | pure copy | hybrid | saved |
|---|---|---|---|
| 1 | 25.7 d | 21.7 d | 4.0 d |
| 2 | 39.6 d | 31.2 d | 8.4 d |
| 5 | 81.2 d | 66.3 d | 14.9 d |

With the BPO in hand there is no reason to copy the ship at all at
low N — the copy pipeline exists for parallelism, and a single-run
BPC provides none. The second-BPO question (M12's ladder) starts at
"acquire a second Charon BPO" only if N grows past where the
sequential copy queue outruns the reaction phases' delivery.

**Blueprint-acquisition assumption (decided 2026-11-18)**: the
timelines above model the owned-BPO scenario. Under the
missing-blueprint default — purchase the Charon BPC off contract —
procurement lead replaces the copy queue entirely: chain end ≈
max(inputs ready, procurement lead) + build. At ×1 that is
max(9.9 d, L) + 11.8 d ≈ **21.7 d** whenever the contract fills
inside the reaction phases — the same end as hybrid, without owning
the BPO. The single-run BPC makes the Charon the cleanest possible
case for contract purchase: nothing about the copy pipeline matters
at low N.

## Findings and caveats

- **Chain resolves end to end with zero model changes** — 7 phases,
  ≈120 aggregated nodes, 60 terminator types. The only script change
  the Charon forced: four new `RAW_CATEGORIES` entries (the
  unclassified-terminator report did its job).
- **Mixed-phase scheduling is approximate**: phases 2–4 mix
  manufacturing and reaction items, so reaction durations flow
  through the slot-hour formula instead of the BPO-bound reaction
  branch. Refining this is M9 model work, not a blocker — the
  approximation errs on the slow side (slot-hours ≥ BPO-bound time
  when slots are the constraint, which they are not here either).
- **Recurring commodities** (see Mechanics) — the per-phase build
  treatment is the parked pipelining question made concrete; a
  merged-campaign option would shrink phases 2–3 further.
- **Charon copy critical path** — with one BPO and maxProductionLimit
  1, the ship copy is ≈13.9 d per unit. The realistic plan is
  direct-from-BPO for the ship itself (hybrid, above) with copies
  reserved for the parallelizable components — or, per the
  missing-blueprint default, simply purchase the single-run Charon
  BPC off contract and skip the copy question entirely.
