# The Strong Crash booster chain — full reference

Seventh chain document (after `TYPHOON-CHAIN.md` through
`RAGE-CHAIN.md`), added 2026-11-20 for the **reaction-terminal**
roadmap step: the deliverable rides a three-tier biochemical
reaction stack, validating that the workflow isn't
manufacturing-centric at the target level. The set piece is the
**cross-drug dependency web** — the first genuinely DAG-shaped chain
in the program: an Improved booster consumes the *Pure Standard*
forms of **two different drugs**, and the Strong tier adds a third,
so building Strong Crash means simultaneously running the Standard
Crash, Standard Blue Pill, and Standard Frentix lines. Every
deterministic number here is output of the reference scripts —
regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 10152 100
```

Provenance: read from the live SDE (Static Data Export) mirror
(release 2026-11-13) and the synced live tables (ownership, skills,
stock — 2026-11-20). Phases count up in build order (terminators =
phase 0, target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Strong Crash Booster ×100)

- IDs: Strong Crash Booster **10152**, Blueprint **25311**
  ('Booster Blueprints' group; maxProductionLimit **100** — ×100 is
  exactly one max job; 20 min/run, so the manufacturing cap is
  33.3 h total). Product of a **five-formula reaction stack**:
  Standard Crash **46231**, Standard Blue Pill, Standard Frentix,
  Improved Crash **46236**, Strong Crash **46244** — all 3 h/run.
- **The cross-drug DAG**: Strong Crash ← Pure Improved Crash (12/run),
  Pure Standard Frentix (15/run), Hydrochloric Acid 20, N blocks 5;
  Pure Improved Crash ← Pure Standard Crash (15), Pure Standard
  Blue Pill (15), Spirits 20, N blocks 5; each Pure Standard line ←
  its cytoserocin gas 20, Water 20, a fuel block 5 (Nitrogen for
  Crash/Blue Pill, **Helium for Frentix**). Building Strong Crash
  means three gas-harvesting lines and three reaction tiers, with
  sibling-drug edges no tree-shaped chain has shown before.
- **Batch cascade with deterministic over-delivery**: the reaction
  yields (15, 15, 15, 12, 12) and the consumptions (15+15, 12+15,
  11-per-booster) align almost exactly at ×100 — 92 runs per
  reaction tier covers every need, with Pure Strong Crash over-
  delivering 1,104 against 1,100 (4 spare) and the fuel-block
  levels rounding 11.5 → 12 twice (Nitrogen 1,880 made vs 1,840;
  Helium 480 vs 460). The intermediate layer's batch minimums are
  the reaction analog of the Rage chain's finding, now stacked three
  tiers deep.
- **The recurring commodity at three levels**: Nitrogen Fuel Block
  appears at phases 3, 2, and 1 (460 + 460 + 920 — the strong,
  improved, and standard tiers' fuel), Water at phases 2 and 1
  (1,840 + 3,680). The level-split rounding costs one extra
  Nitrogen-block run (47 level-split vs 46 merged) — the first
  concrete price tag on the merged-campaign question (M5/M9): the
  recurring-commodity entry now has a number, not just a shape.
- Skills: **Reactions 2 / 3 / 4** by tier (held live — four
  characters at Reactions 5) and **Drug Manufacturing 1 / 3 / 5** by
  booster tier — a new skill family, and the Strong tier's level-5
  gate is held by **nobody on the roster** (simulated per the
  2026-11-19 convention; this chain's sole live gap).
- **The reaction stack is the plan**: 460 reaction runs × 3 h ≈
  1,380 slot-hours across five formulas (92 per tier) against the
  33.3 h manufacturing cap and trivial fuel-block builds — at ×100,
  ~95% of the plan's work is reactions. Serial-phase wall-clock
  (roster-size concurrency per formula, ~6 characters): ≈ 2 d per
  tier × 3 tiers + 1.4 d manufacturing ≈ **7.4 d illustrative**.
- **New terminators**: three k-space cytoserocins (Golden, Amber,
  Lime — 'Harvestable Cloud' group, gas-site harvesting or market;
  1,840 each) and two producer-less NPC trade goods — Spirits
  ('General' group) and Hydrochloric Acid ('Biohazard' group),
  1,840 each. Water (5,520 needed vs 110,337 stocked) and Megacyte
  (800 vs 5,117) are covered.
- **From zero**: no booster formulas, no booster blueprints, no gas
  — the first fully from-zero chain since the Charon (the Rage and
  Trimark rode owned pools).
- **Contraband**: boosters are contraband in high-security space
  (customs seizure risk on transport) — a logistics constraint the
  market layer (M10) and any delivery modeling must carry; the SDE
  does not encode it (community-documented).
- Structure note: biochemical reactions may have their own facility
  requirements (the historical drug-lab array) — **pin at M3**
  whether the structure manager's reaction facilities cover
  biochemical formulas or need a separate class.

## Per-branch tree (Strong Crash Booster ×100)

```text
- Strong Crash Booster x100 [manufacturing] (100 runs, 1/run)
  - Megacyte x800  [raw]
  - Pure Strong Crash Booster x1,100 [reaction] (92 runs, 12/run)
    - Nitrogen Fuel Block x460 [manufacturing] (12 runs, 40/run)
      - Robotics x12  [raw]
      - Enriched Uranium x48  [raw]
      - Mechanical Parts x48  [raw]
      - Coolant x108  [raw]
      - Strontium Clathrates x240  [raw]
      - Oxygen x264  [raw]
      - Heavy Water x2,040  [raw]
      - Liquid Ozone x4,200  [raw]
      - Nitrogen Isotopes x5,400  [raw]
    - Pure Improved Crash Booster x1,104 [reaction] (92 runs, 12/run)
      - Nitrogen Fuel Block x460 [manufacturing] (12 runs, 40/run)
        - Robotics x12  [raw]
        - Enriched Uranium x48  [raw]
        - Mechanical Parts x48  [raw]
        - Coolant x108  [raw]
        - Strontium Clathrates x240  [raw]
        - Oxygen x264  [raw]
        - Heavy Water x2,040  [raw]
        - Liquid Ozone x4,200  [raw]
        - Nitrogen Isotopes x5,400  [raw]
      - Pure Standard Blue Pill Booster x1,380 [reaction] (92 runs, 15/run)
        - Nitrogen Fuel Block x460 [manufacturing] (12 runs, 40/run)
          - Robotics x12  [raw]
          - Enriched Uranium x48  [raw]
          - Mechanical Parts x48  [raw]
          - Coolant x108  [raw]
          - Strontium Clathrates x240  [raw]
          - Oxygen x264  [raw]
          - Heavy Water x2,040  [raw]
          - Liquid Ozone x4,200  [raw]
          - Nitrogen Isotopes x5,400  [raw]
        - Water x1,840  [raw]
        - Amber Cytoserocin x1,840  [raw]
      - Pure Standard Crash Booster x1,380 [reaction] (92 runs, 15/run)
        - Nitrogen Fuel Block x460 [manufacturing] (12 runs, 40/run)
          - Robotics x12  [raw]
          - Enriched Uranium x48  [raw]
          - Mechanical Parts x48  [raw]
          - Coolant x108  [raw]
          - Strontium Clathrates x240  [raw]
          - Oxygen x264  [raw]
          - Heavy Water x2,040  [raw]
          - Liquid Ozone x4,200  [raw]
          - Nitrogen Isotopes x5,400  [raw]
        - Water x1,840  [raw]
        - Golden Cytoserocin x1,840  [raw]
      - Spirits x1,840  [raw]
    - Pure Standard Frentix Booster x1,380 [reaction] (92 runs, 15/run)
      - Helium Fuel Block x460 [manufacturing] (12 runs, 40/run)
        - Robotics x12  [raw]
        - Enriched Uranium x48  [raw]
        - Mechanical Parts x48  [raw]
        - Coolant x108  [raw]
        - Strontium Clathrates x240  [raw]
        - Oxygen x264  [raw]
        - Heavy Water x2,040  [raw]
        - Liquid Ozone x4,200  [raw]
        - Helium Isotopes x5,400  [raw]
      - Water x1,840  [raw]
      - Lime Cytoserocin x1,840  [raw]
    - Hydrochloric Acid x1,840  [raw]
```

## Aggregated phases (shared intermediates merged)

### Phase 5

| Type | Required | Activity / runs |
|---|---:|---|
| Strong Crash Booster | 100 | manufacturing, 100 runs |

### Phase 4

| Type | Required | Activity / runs |
|---|---:|---|
| Megacyte | 800 | raw (terminator) |
| Pure Strong Crash Booster | 1,100 | reaction, 92 runs |

### Phase 3

| Type | Required | Activity / runs |
|---|---:|---|
| Hydrochloric Acid | 1,840 | raw (terminator) |
| Nitrogen Fuel Block | 460 | manufacturing, 12 runs |
| Pure Standard Frentix Booster | 1,380 | reaction, 92 runs |
| Pure Improved Crash Booster | 1,104 | reaction, 92 runs |

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 12 | raw (terminator) |
| Enriched Uranium | 48 | raw (terminator) |
| Mechanical Parts | 48 | raw (terminator) |
| Coolant | 108 | raw (terminator) |
| Strontium Clathrates | 240 | raw (terminator) |
| Oxygen | 264 | raw (terminator) |
| Heavy Water | 2,040 | raw (terminator) |
| Liquid Ozone | 4,200 | raw (terminator) |
| Nitrogen Isotopes | 5,400 | raw (terminator) |
| Spirits | 1,840 | raw (terminator) |
| Water | 1,840 | raw (terminator) |
| Lime Cytoserocin | 1,840 | raw (terminator) |
| Nitrogen Fuel Block | 460 | manufacturing, 12 runs |
| Helium Fuel Block | 460 | manufacturing, 12 runs |
| Pure Standard Blue Pill Booster | 1,380 | reaction, 92 runs |
| Pure Standard Crash Booster | 1,380 | reaction, 92 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 24 | raw (terminator) |
| Enriched Uranium | 96 | raw (terminator) |
| Mechanical Parts | 96 | raw (terminator) |
| Coolant | 216 | raw (terminator) |
| Strontium Clathrates | 480 | raw (terminator) |
| Oxygen | 528 | raw (terminator) |
| Heavy Water | 4,080 | raw (terminator) |
| Liquid Ozone | 8,400 | raw (terminator) |
| Nitrogen Isotopes | 5,400 | raw (terminator) |
| Water | 3,680 | raw (terminator) |
| Amber Cytoserocin | 1,840 | raw (terminator) |
| Golden Cytoserocin | 1,840 | raw (terminator) |
| Helium Isotopes | 5,400 | raw (terminator) |
| Nitrogen Fuel Block | 920 | manufacturing, 23 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Robotics | 23 | raw (terminator) |
| Enriched Uranium | 92 | raw (terminator) |
| Mechanical Parts | 92 | raw (terminator) |
| Coolant | 207 | raw (terminator) |
| Strontium Clathrates | 460 | raw (terminator) |
| Oxygen | 506 | raw (terminator) |
| Heavy Water | 3,910 | raw (terminator) |
| Liquid Ozone | 8,050 | raw (terminator) |
| Nitrogen Isotopes | 10,350 | raw (terminator) |

Read the phase tables against the tree: the **same type at multiple
levels** is the whole story of this chain's shape. Nitrogen Fuel
Block carries the strong tier's fuel at phase 3, the improved tier's
at phase 2, and both standard lines' at phase 1 (merged 920);
Water feeds the standard lines at phase 2 and recurs at phase 1.
The Pure intermediates never recur — each drug line is its own
subtree — but they **cross-reference** (Improved consumes Crash and
Blue Pill lines), which is why this is a DAG rather than a tree.

## Raw-material acquisition table (Strong Crash Booster ×100)

| Gas (harvestable clouds) | Required |
|---|---:|
| Amber Cytoserocin | 1,840 |
| Golden Cytoserocin | 1,840 |
| Lime Cytoserocin | 1,840 |

| NPC market good | Required |
|---|---:|
| Spirits | 1,840 |
| Hydrochloric Acid | 1,840 |

| Ice product | Required |
|---|---:|
| Nitrogen Isotopes | 21,150 |
| Liquid Ozone | 20,650 |
| Heavy Water | 10,030 |
| Helium Isotopes | 5,400 |
| Oxygen | 1,298 |
| Strontium Clathrates | 1,180 |

| PI commodity | Required |
|---|---:|
| Water | 5,520 |
| Coolant | 531 |
| Enriched Uranium | 236 |
| Mechanical Parts | 236 |
| Robotics | 59 |

| Mineral | Required |
|---|---:|
| Megacyte | 800 |

Twenty raw types. The genuine acquisition story is the **gas
harvest** — 1,840 units of each cytoserocin, k-space gas-site
clouds (or market) — plus the two NPC trade goods; the entire ice
and PI stack exists only to fuel the reaction tiers' fuel blocks
(47 Nitrogen runs + 12 Helium runs), and Water/Megacyte are covered
by stock many times over.

## Blueprint inventory (live, 2026-11-20)

| Blueprint | Activity | Status |
|---|---|---|
| Strong Crash Booster Blueprint | manufacturing | **not owned** — the target's BP ('Booster Blueprints' group); acquisition path unverified (candidates: NPC-seeded market original, LP store, or drop — **pin, verify against M15**) |
| Standard Crash Booster Reaction Formula | reaction | not owned — NPC-seeded original per the reaction-formula precedent (verify M15) |
| Standard Blue Pill Booster Reaction Formula | reaction | not owned — same |
| Standard Frentix Booster Reaction Formula | reaction | not owned — same |
| Improved Crash Booster Reaction Formula | reaction | not owned — same |
| Strong Crash Booster Reaction Formula | reaction | not owned — same |

Six blueprints, none owned — the from-zero acquisition story is six
cheap originals (five formulas at the reaction-formula precedent's
price class, one booster BP at a pin). No invention, no copying, no
contract backfill: the simplest blueprint tier since the Trimark's
three.

## Mechanics the expansion established

- **Cross-drug dependencies make the chain a DAG**: the Improved and
  Strong tiers consume sibling drugs' Pure Standard forms, so the
  requirement graph has cross edges between drug lines. The walk
  handles it (the expansion is a DAG traversal), but M5's resolver
  must expect it — cycle detection is already mandated defensively,
  and sibling-edge sharing means **campaign aggregation matters
  more than tree chains**: three lines share the Water, fuel-block,
  and ice stacks, and merging them is where the savings live.
- **The reaction stack is the plan's body**: at ×100, reactions hold
  ~95% of the slot-hours (1,380 of ~1,450) and all three serial
  phase gaps. The manufacturing cap is one 33.3 h job. The inverse
  of the Charon (build-dominated) and Jackdaw (single-build-
  dominated) profiles: a **reaction-dominated** bar, the shape the
  roadmap step set out to validate.
- **Batch-cascade over-delivery, three tiers deep**: near-unity
  yield/consumption ratios (15/15, 12/12, 11-per-unit) align at ×100
  with only small surpluses (4 Pure Strong, 40 Nitrogen blocks, 20
  Helium blocks) — but at other target counts the ratios misalign
  harder, and the surplus cascades multiplicatively down the tiers.
  Target selection interacts with batch alignment — an M6/M9
  planning-surface the Rage chain hinted at and this chain makes
  unavoidable.
- **Recurring-commodity cost is now measurable**: the level-split
  phases round fuel-block runs up twice (11.5 → 12 at two levels),
  buying 40 extra Nitrogen blocks against the merged campaign's 46
  runs. Small here; the principle scales — merged campaigns need
  per-type run rounding exactly once, level-split once per level.
- **New skill family**: Drug Manufacturing gates the manufacturing
  cap at 1/3/5 by booster tier (nobody holds it — simulated per
  convention), while Reactions 2/3/4 gate the stack (held). The
  first chain where the *reaction* gates are live and the
  *manufacturing* gate is the simulated one — the mirror image of
  every previous set.

## Findings and caveats

- **From-zero, shopping-list acquisition**: six blueprints, two NPC
  trade goods, three gases; everything else is stock or trivially
  small. The meters' story is gas volume, not breadth.
- **Gas-site volume**: 1,840 units per cytoserocin is a real
  harvesting campaign (or a market trip) — the M14 farming flow's
  second natural customer after the Jackdaw's salvage stack.
- **Contraband logistics** (community-documented, not in SDE):
  highsec transport risks customs seizure — a constraint for M10
  market modeling and any delivery/farming flow; pin the exact
  mechanics when M10 opens.
- **Biochemical reaction facilities** — pin at M3 whether the
  structure manager needs a distinct facility class for biochemical
  formulas (the historical drug-lab array) or refinery reaction
  slots cover them.
- **Booster BP acquisition** — pin, verify against M15 market data.
- Skills simulated only for Drug Manufacturing 5 (nobody holds it);
  every reaction gate is held live.
- The Standard and Improved **booster** blueprints (which
  manufacture the sellable lower-tier boosters) are deliberately
  not in this chain — the plan consumes the Pure intermediates, not
  the lower-tier boosters. A multi-tier product-line plan (sell
  Standard surplus *and* Strong) is a possible future target-set
  feature, not a chain mechanic — the same boundary the subsystems
  correction drew.
