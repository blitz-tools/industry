# The Large Trimark Armor Pump II chain — full reference

Fifth chain document (after `TYPHOON-CHAIN.md`, `CHARON-CHAIN.md`,
`PANTHER-CHAIN.md`, and `JACKDAW-CHAIN.md`), added 2026-11-20 for the
**T2 (Tech 2) rig** half of the rigs-and-ammo roadmap step: invention at
medium volume (ten successes at 34% — the set's first multi-success
invention plan), the first non-ship deliverable, a brand-new terminator
class (wreck salvage), manufacturing capped at one run per job
(maxProductionLimit 1 — volume scales job count, not job size), and the
first chain to size its **invention-input copy layer** (2026-11-20
direction: plans copy their invention inputs from BPOs rather than
assuming BPC inventory — BPC count as the invention-parallelism knob,
copy throughput bound by the corporation's two source BPOs; earlier
chains' copy strategies sized copies for *manufacturing*, not for
invention attempts).
Every deterministic number here is output of the reference scripts —
regenerate with:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 26302 10
```

Provenance: read from the live SDE (Static Data Export) mirror (release
2026-11-13) and the synced live tables (ownership, skills, stock —
2026-11-20). Phases count up in build order (terminators = phase 0,
target = highest); math symbols stay unexpanded — see
`reference/GLOSSARY.md`.

## Key facts (Large Trimark Armor Pump II ×10)

- IDs: Large Trimark Armor Pump II **26302**, Blueprint **26303**
  (maxProductionLimit **1**, 12.5 h build per unit). Invented from
  Large Trimark Armor Pump I Blueprint **25895** (maxProductionLimit 40)
  at **34%** — the middle rung of the probability ladder this program
  has measured (Panther 22%, T3 relic grades 26/21/14%).
- **One BPC per success** (SDE activity-8 product quantity 1): ×10
  needs ten independent invention successes. Expected attempts per
  success = 1/p = 2.94; for ten successes E[attempts] = 29.4, and the
  binomial confidence table is the planning surface the single-success
  chains never exposed: P(≥10 successes) = 33% at n=25, **55% at the
  expected 29**, 60% at 30, 80% at 35, 92% at 40, 97% at 45. Planning
  to expected value under-supplies half the time — the plan must buy
  attempts to a confidence target, not to the mean.
- Skills: invention Hydromagnetic Physics 1, Nanite Engineering 1,
  Amarr Encryption Methods 1; manufacturing Industry 5, Nanite
  Engineering 1, Hydromagnetic Physics 1, **Armor Rigging 3** — the
  first build gate in the program that requires a skill above level 1
  outside the Industry line. Live check 2026-11-20: the rigging gate is
  genuinely held (blitzrage 4, theblitzrage 4, Storm Ragez 3) and both
  sciences are at 4; **nobody holds Amarr Encryption Methods** (the
  sole live gap — simulated per the 2026-11-19 convention, which this
  chain's set follows).
- Attempt time **6.5 h** (between the Jackdaw's 1 h and the Panther's
  53.33 h); 3 + 3 datacores per attempt (Nanite Engineering +
  Hydromagnetic Physics); expected ≈ 88 + 88 for ten successes — on
  hand: 21 and 30. The widest datacore shortfall relative to need in
  the program so far.
- Rig inputs: **Intact Armor Plates ×200, Interface Circuit ×230,
  Nanite Compound ×150 + R.A.M.- Armor/Hull Tech ×10** — pure wreck
  salvage plus one R.A.M. run. No components, no reactions, no nested
  T1 product: at three phases this is the shallowest chain in the set
  (the Jackdaw needed five, the Charon seven).
- **New terminator class: wreck salvage** ('Salvaged Materials' group,
  41 types, maps cleanly) — k-space wreck drops via salvager module,
  market-acquired, no producing blueprint. Rig manufacturing comes in
  condition tiers off the same salvage families: T1 rigs eat the
  damaged variants (Fried Interface Circuit, Contaminated Nanite
  Compound, plain Armor Plates), T2 the intact ones (Interface
  Circuit, Nanite Compound, Intact Armor Plates). Live stock of all
  three intact types: **zero** — acquisition is the entire raw story.
- **maxProductionLimit 1**: the T2 rig blueprint cannot stack runs
  into one job — ten rigs are ten separate 12.5 h jobs, one per BPC,
  and blueprint job-lock makes manufacturing concurrency equal to
  invention successes in hand. Volume scales job count, not job size
  — the exact opposite of the Charon's 20,000-run component jobs and
  the closest thing to per-unit overhead (installation cost ×10) the
  program has modeled.
- **The copy layer is modeled from zero** (2026-11-20 direction): the
  plan copies its invention inputs from the corporation's two Large
  Trimark Armor Pump I BPOs (ME 10 / TE 20) rather than assuming BPC
  inventory — sizing analysis in the Copy layer section below. The
  corporation's existing 130 runs of T1 BPCs (2 × 40-run max-run,
  5 × 10-run) remain an availability overlay that can zero the copy
  phase; the reference chain models the copies so the planner has the
  from-zero shape either way.
- Durations: T1 copy **1 h/run** (one copy job per BPO at a time —
  the two BPOs bound copy throughput at 2 runs/h), invention
  6.5 h/attempt, rig build 12.5 h/unit, R.A.M. 42 min (one run of
  100). **Wall-clock hinges on BPC sizing, not invention volume**:
  invention's ≈ 191 expected slot-hours compress to a single 6.5 h
  wave when every attempt gets its own BPC (the slot pool allows it),
  leaving **the copy phase owning the timeline** (≈ 18 h BPO-bound)
  ahead of manufacturing (12.5 h). The mirror image of the Jackdaw's
  build-dominated bar is a copy-dominated one.

## Per-branch tree (Large Trimark Armor Pump II ×10)

```text
- Large Trimark Armor Pump II x10 [manufacturing] (10 runs, 1/run)
  - Intact Armor Plates x200  [raw]
  - Nanite Compound x150  [raw]
  - R.A.M.- Armor/Hull Tech x10 [manufacturing] (1 runs, 100/run)
    - Tritanium x556  [raw]
    - Pyerite x444  [raw]
    - Mexallon x222  [raw]
    - Isogen x82  [raw]
    - Nocxium x36  [raw]
  - Interface Circuit x230  [raw]
```

## Aggregated phases (shared intermediates merged)

### Phase 2

| Type | Required | Activity / runs |
|---|---:|---|
| Large Trimark Armor Pump II | 10 | manufacturing, 10 runs |

### Phase 1

| Type | Required | Activity / runs |
|---|---:|---|
| Intact Armor Plates | 200 | raw (terminator) |
| Nanite Compound | 150 | raw (terminator) |
| Interface Circuit | 230 | raw (terminator) |
| R.A.M.- Armor/Hull Tech | 10 | manufacturing, 1 runs |

### Phase 0

| Type | Required | Activity / runs |
|---|---:|---|
| Tritanium | 556 | raw (terminator) |
| Pyerite | 444 | raw (terminator) |
| Mexallon | 222 | raw (terminator) |
| Isogen | 82 | raw (terminator) |
| Nocxium | 36 | raw (terminator) |

## Raw-material acquisition table (Large Trimark Armor Pump II ×10)

| Mineral | Required |
|---|---:|
| Tritanium | 556 |
| Pyerite | 444 |
| Mexallon | 222 |
| Isogen | 82 |
| Nocxium | 36 |

| Wreck salvage | Required |
|---|---:|
| Interface Circuit | 230 |
| Intact Armor Plates | 200 |
| Nanite Compound | 150 |

Eight raw types, three of them new-class terminators — the smallest
acquisition surface in the program (the Jackdaw's was 43 types).
Mineral stock covers everything except Isogen (0 on hand vs 82
required). R.A.M.- Armor/Hull Tech is NPC-seeded like every R.A.M.
(the Jackdaw chain's fourth acquisition path).

## Copy layer (invention inputs)

The plan's invention attempts consume runs of the T1 source BPC — one
run per attempt, and **one active job per blueprint** — so the number
of BPCs copied is the invention-parallelism knob, set before anything
else installs. Copy jobs take runs × 1 h each (one job per BPO at a
time; the corporation holds two BPOs), which makes total copy time
**split-invariant**: 2 × 18-run copies and 35 × 1-run copies cost the
same BPO-hours, so the split is a pure parallelism decision with no
copy-time penalty.

The sizing rule:

- **BPC count = min(attempt budget, invention slot pool)** — every BPC
  below that bound is a free parallelism gain; past the slot pool
  (characters × 10 at max skills, separate pools per activity) extra
  BPCs are dead weight.
- **Runs per BPC = ⌈attempt budget ÷ BPC count⌉** — sized to the
  confidence budget, not to maxProductionLimit (40 here; never
  binding when sizing for parallelism).
- Copy wall-clock = total runs × 1 h ÷ 2 BPOs (BPO-bound); invention
  wall-clock = ⌈attempts ÷ BPC count⌉ × 6.5 h.

Worked sizings for the ×10 plan's 35-attempt budget (80% confidence;
copy wall quantized by job packing on 2 BPOs; plan total adds the
12.5 h manufacturing wave):

| Sizing | Copy wall | Invention waves | Invention wall | Plan total |
|---|---:|---:|---:|---:|
| 2 BPCs × 18 runs | 18 h | 18 | 117 h | 147.5 h |
| 8 BPCs × 5 runs | 20 h | 5 | 32.5 h | 65 h |
| 20 BPCs × 2 runs | 20 h | 2 | 13 h | 45.5 h |
| 35 BPCs × 1 run | 18 h | 1 | 6.5 h | 37 h |

Three consequences:

1. **The copy phase owns the wall-clock at full parallelism** — 18 h
   BPO-bound against invention's compressed 6.5 h and manufacturing's
   12.5 h. The BPC-count decision is worth ~4× wall-clock, and the
   corporation's **two BPOs are the bottleneck asset**: a third cuts
   the copy floor to ~12 h (the M12 min-BPO analysis applies to the
   copy queue exactly as it did to the Typhoon's).
2. **All-parallel commits the full budget before any information**:
   35 attempts in flight spend all 105 + 105 datacores even if early
   successes would have stopped the plan at ten. Staging (smaller
   BPC count, more waves) trades wall-clock for early-stop savings —
   ~5 attempts in expectation at 34%, small but a real knob. Copying
   in increments hedges the same way on the copy side.
3. **The copy phase doesn't need to finish before invention starts**:
   a completed 1-run copy can begin inventing while later copies
   still run — a pure hand-off with no material dependency, the
   cheapest pipelining edge in the model. The serial phases here
   keep them separate per convention; flag for M9.

The owned-inventory overlay: the corporation's 130 runs of existing
T1 BPCs (2 × 40-run, 5 × 10-run) exceed the 35-attempt budget almost
fourfold, so a planner that checks source-BPC stock before scheduling
copies zeroes this phase entirely — the availability check is
"source-BPC runs ≥ attempt budget", the same meter shape the Rage
chain applies to invented-BPC run pools. The from-zero chain above is
the reference shape; the stock is the live shortcut.

**Destination note**: this chain's copy layer is the pure
**Copy → Invention** case — every copied run feeds an invention
attempt (1 run per attempt, burned on success or failure, budget =
the confidence-targeted 35). The other destination, **Copy →
Manufacturing** (the Typhoon chain's copy-vs-direct economics), is
structurally impossible here at the T2 level: T2 rig BPCs are
invention products, and copies cannot themselves be copied —
manufacturing from them has no copy option. The two destinations
coexist in one copy wave when the invention source's T1 product is
also a build input — the Panther is the recorded example (its
Typhoon BPC pool feeds both invention attempts and the hull build),
and the shared BPO queue must merge both demands with per-destination
run earmarking. See MILESTONES.md's copy-destinations entry.

## Invention layer (Large Trimark Armor Pump II Blueprint)

Source: Large Trimark Armor Pump I Blueprint (**25895**, activity 8,
invention). Probability **0.34** base (SDE); skill levels are assumed
NOT to modify it post-Crius — pin at M8.

- Materials per attempt: 3 Datacore - Nanite Engineering, 3 Datacore -
  Hydromagnetic Physics. Skills: Hydromagnetic Physics 1, Nanite
  Engineering 1, Amarr Encryption Methods 1.
- T1 consumption: 1 run of the source BPC per attempt (implicit in the
  game, absent from the SDE material list). The corporation's 130 runs
  of owned T1 BPCs cover the expected 29.4 attempts more than four
  times over.
- BPC runs per success: **1** (SDE activity-8 product quantity). Owned
  BPCs report their ESI-synced runs instead — see the live-BPC
  reconciliation below.

Ten successes needed; expected attempts per success 2.94, so
E[attempts] = 29.4 and E[datacores] ≈ 88 + 88 (on hand: 21 + 30).
Confidence for the full ×10, P(≥10 successes in n attempts):

| Attempts | 25 | 29 (E) | 30 | 35 | 40 | 45 |
|---|---:|---:|---:|---:|---:|---:|
| P(≥10) | 33% | 55% | 60% | 80% | 92% | 97% |

Decryptor scenarios (modifiers pinned from live ESI dogma 2026-11-19;
invented-BPC base ME/TE −4/−4 per community docs — challenged by the
live-BPC evidence below, pin at M8):

| Decryptor | p_eff | E[attempts]/success | ME_eff | TE | runs |
|---|---:|---:|---:|---:|---:|
| (none) | 0.34 | 2.94 | −4 | −4 | 1 |
| Accelerant | 0.41 | 2.45 | −2 | +10 | 2 |
| Attainment | 0.61 | 1.63 | −5 | +4 | 5 |
| Augmentation | 0.20 | 4.90 | −6 | +2 | 10 |
| Parity | 0.51 | 1.96 | −3 | −2 | 4 |
| Process | 0.37 | 2.67 | −1 | +6 | 1 |
| Symmetry | 0.34 | 2.94 | −3 | +8 | 3 |
| Optimized Attainment | 0.65 | 1.55 | −3 | −2 | 3 |
| Optimized Augmentation | 0.31 | 3.27 | −2 | +0 | 8 |

Decryptors cut both ways for a ten-success plan: probability
multipliers compound across successes (Attainment drops E[attempts]
from 29.4 to 16.3), while run modifiers above the maxProductionLimit-1
job shape are wasted — a 5-run BPC still builds one rig per job, the
extra runs only save later inventions. The T2 rig decryptor question
is therefore attempts-vs-cost, with no ship-style runs payoff.

### Retry semantics (under-delivery and residue)

Ten successes at 34% is the program's first plan where invention can
under-deliver a multi-unit target, so the loop semantics matter here
(MILESTONES.md's retry-semantics entry, 2026-11-20):

- **The target never silently shrinks** — 10 rigs is the requirement;
  7 successes after the budget is a blocked plan with an owner
  decision (extend budget, escalate decryptor, buy BPCs, descope),
  not a 7-rig plan with stranded materials.
- **The loop**: attempts go out in batches (the Copy layer's BPC
  pool), successes counted from synced `industry_jobs` after each
  batch, the next batch re-armed to the remaining need at the
  confidence target. At the 80%/35 budget the plan *expects* to
  finish with residue: E[successes] = 11.9 against 10 — roughly
  **2 surplus BPCs of BPC residue**, banked for future plans, never
  inflating this target. Material residue (provisioned salvage held
  while blocked) stays visible against the plan until completion or
  descope.
- **Display requirements for the set's build-plan pages**: invention
  job cards carry p_eff with the base→effective breakdown and the
  decryptor's modifiers; wave cards carry batch size, P(≥ remaining
  target in batch), and cumulative successes/attempts; the
  active-plan page shows the loop mid-flight (e.g. 7/10 successes,
  batch 2 scheduled with cause). The Trimark set is the vehicle for
  these — the Rage set carries the over-delivery half (its 8 spare
  runs are BPC residue as a live example).

### Live-BPC reconciliation (M8 pin evidence, 2026-11-20)

The roster holds thirteen invented T2 rig BPCs across types (Capital
Trimark II, Capital Warhead Rigor Catalyst II, Medium Burst Aerator
II, …) — every one reads **2 runs, ME 0, TE 0** from the live
blueprints table against an SDE activity-8 product quantity of 1. No
row in the pinned decryptor table converts any candidate base into
(2, 0, 0): from base (1, −4, −4) it would take (+1, +4, +4); from the
2/4 base that the Scourge Rage chain's reconciliation supports
(`RAGE-CHAIN.md`), (+1, −2, −4). Candidates: a rig-specific base-runs
value of 2 with base ME/TE 0/0, contract-purchased BPCs from someone
else's inventions, or an older invention era. **Pin at M8** — until
then, projections use the SDE quantity (1) and owned BPCs render
their synced values, which is exactly the split the planner should
ship: inventory is read, projections are computed.

## Blueprint inventory (live, 2026-11-20)

| Blueprint | Activity | Status |
|---|---|---|
| Large Trimark Armor Pump II Blueprint | invention product | **not owned** — the plan's ten inventions |
| Large Trimark Armor Pump I Blueprint | invention source | owned, corporation — 2 originals (ME 10 / TE 20) + 7 BPCs (2 × 40-run, 5 × 10-run; 130 runs) |
| R.A.M.- Armor/Hull Tech Blueprint | manufacturing | not owned — NPC-seeded market original |

Three blueprints, two owned outright — the inverse of the Jackdaw's
23-blueprint inventory. The one acquisition (R.A.M.) is the cheapest
path in the program's catalog.

## Mechanics the expansion established

- **Invention at medium volume is binomial planning**: ten successes
  at 34% puts the plan on the P(≥k | n) curve, not the per-BPC
  expected-value math of the single-success chains. Buying to E = 29.4
  attempts succeeds 55% of the time; an 80% plan buys 35, a 95% plan
  buys ~44. The planner needs a confidence knob on multi-success
  invention, the same "attempts to buy" decision the Jackdaw made for
  one success at 26%.
- **maxProductionLimit 1 reshapes job math**: k = min(maxProductionLimit,
  runs) collapses to 1, jobs = runs, and the even-split rule is vacuous.
  Per-job installation overhead is now linear in target size — the
  cost model (M4) must not assume amortization.
- **Manufacturing concurrency is bounded by invention, not slots**:
  job-lock ties each of the ten jobs to its own 1-run BPC, so the
  build phase's parallelism is literally the invention phase's success
  count arriving. The wave bar should show the mfg phase widening as
  inventions land (pipelining question, M9 — the serial model here
  keeps them phase-separated).
- **Wreck salvage enters the acquisition model**: a third
  market-acquired, non-buildable material class (after moon materials
  and Sleeper salvage), with the T1/T2 condition-tier pairing as a
  market-relationship the buy-vs-build layer (M10) can surface —
  damaged-tier supply is irrelevant to a T2 rig plan and vice versa.
- **Copy sizing is a first-class planning decision** (Copy layer
  section): BPC count is the invention-parallelism knob, copy time is
  split-invariant, so the sizing rule is BPC count =
  min(attempt budget, invention slot pool) with runs per BPC =
  ⌈budget ÷ count⌉. The copy phase is BPO-bound and can own the
  wall-clock — BPO count is a bottleneck asset the M12 BPO-recommendation
  analysis already covers for copy queues.
- **Invention-input sufficiency is an availability check, not a
  schedule**: source-BPC runs (130 owned) against attempts bought (35
  at 80%) is one comparison in the same bucket as material meters.
  The copy plan exists only when the comparison fails — but the
  from-zero chain always carries its shape.

## Findings and caveats

- **Copy-dominated wave shape at full parallelism** (from-zero, 35
  BPCs): copy ≈ 18 h (BPO-bound) vs invention 6.5 h (slot-compressed)
  vs manufacturing 12.5 h — plan ≈ 37 h ≈ 1.5 days. Invention still
  holds the most *slot-hours* (≈ 191 expected vs 125 manufacturing),
  but slots are abundant; the BPO-bound copy phase is the wall-clock
  owner. Under the owned-inventory overlay the copy wave disappears
  and invention (6.5 h) → manufacturing (12.5 h) is the whole bar.
  Either way the plan's real end-date is a confidence band (the
  invention phase is probabilistic) — M9 must decide how a plan
  renders a P80 end vs an expected end.
- **The 2-run rig BPC discrepancy** (live 2 vs SDE 1) is documented in
  the reconciliation above — the second live counterexample to the
  SDE-quantity convention, alongside the Rage chain's supporting
  evidence for base ME/TE 2/4.
- **Zero intact-salvage stock** makes the raw story market-pure; the
  availability meters will show three red bars and nothing else in the
  raw tier — a deliberately minimal acquisition surface to contrast
  the volume story on the ammo side.
- **Isogen 0 on hand** (82 required) — trivial, but the only mineral
  gap; the meters should catch it without a special case.
- Skills simulated as met for Amarr Encryption Methods only
  (nobody holds it); every other gate in this chain — including the
  Armor Rigging 3 build gate — is held live (blitzrage 4).
- The T1 rig manufacturing line (damaged salvage → T1 Trimark, the
  corporation's other copy product) is **not part of this chain**: T2
  invention consumes source-BPC runs, not T1 rigs, so the T1 build
  world only matters to this plan as market context for the salvage
  tiers.
