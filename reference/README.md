# Reference — planner proof-out scripts

Executable spec for the industry planner's calculation core. These scripts
regenerate the golden values in `TYPHOON-CHAIN.md` and encode the algorithms
the milestones graduate into the app: chain expansion → M5, time/job math →
M4, scheduling and copy strategy → M9, BPO recommendations → M12. They are
reference implementations, not app code — no ORM, no framework, stdlib only,
read-only against the database.

Run inside the dev container from the repo root:

```sh
podman exec industry_dev_1 python reference/chain_expand.py 644 1
podman exec industry_dev_1 python reference/timeline_model.py 644 100
podman exec industry_dev_1 python reference/timeline_model.py 644 100 \
    --timelines 10,25,50,100
podman exec industry_dev_1 python reference/timeline_model.py 644 100 --bpo
podman exec industry_dev_1 python reference/timeline_model.py 644 100 --horizon
```

`--char <character_id>` runs the model with that character's computed skill
multiplier instead of the max-skills scenario; `--corp <id>` picks the pool.

## Formula reference

Everything is closed-form arithmetic over the SDE mirror (`sde_*` tables)
plus the synced `skills`/`blueprints`/`characters` tables. No LLM at
runtime; nothing here is learned or guessed at run time.

**Chain expansion (M5)**

- producing blueprint: first `industryActivityProducts` row for the type
  (manufacturing = activity 1, copying = 5, reactions = 11 — `ramActivities`
  labels reactions 9, but the data lives on 11)
- runs = ⌈units ÷ products-per-run⌉ (`industryActivityProducts.quantity`:
  components 3/run, fuel blocks 40/run)
- phases: level-by-level aggregation; same-type requirements merge per
  phase, then round runs once — not per parent (the material savings:
  RCF 8 per-branch runs → 7 aggregated)
- terminators: types with no producing blueprint (minerals, moon
  materials, PI commodities, ice products) — leaves to acquire, never
  recursed; raw categories are hardcoded here, M5 classifies via
  invGroups/invCategories
- cycle detection: NOT implemented (T1 manufacturing has none); M5 must
  add it defensively

**Time and job math (M4, M9)**

- per-run times from `industryActivity` (seconds → hours)
- manufacturing time × per-character skill multiplier — **computed from the
  synced `skills` table, never a global constant** (the 0.68 in the
  proof-outs is the max-skills scenario; the roster already diverges —
  theblitzrage holds Advanced Industry 1 → 0.776). The skill→effect mapping
  itself (`MFG_SKILL_MAPPING`) is UNVERIFIED pending the dogma check
- job sizing: k = min(maxProductionLimit, ⌈runs ÷ pool⌉); jobs = ⌈runs ÷ k⌉;
  even split (all jobs end together within one run)
- blueprint job-lock: one active job per blueprint — concurrency per
  commodity = min(slot pool, blueprint count); reactions at 1 BPO per
  character per formula → roster-size concurrency; copying at 1 job per BPO
- login windows: job durations reported in 6h windows (plan parameter)

**Scheduling (M9)**

- serial phases, deepest first; each phase starts at max(previous phase
  end, its commodities' copy-queue ends); the gap is the dead zone
- phase duration = max(longest job, total slot-hours ÷ pool)
- strategies: pure copy; hybrid (copy the longest queue until inputs
  arrive, then build direct — applies when skilled build time < copy time
  per run; break-even multiplier = copy-time ÷ base-build-time, 0.8 across
  this chain); 2×BPO (second BPO for the longest queue)
- copy-vs-direct decision rule and the diminishing-returns analysis:
  see TYPHOON-CHAIN.md

**BPO recommendations (M12)**

- per commodity: queue rate (copy hours per target unit), input-ready rate
  (the next deeper phase's end, fitted linearly — scale-invariant)
- min BPOs = ⌈queue rate ÷ input-ready rate⌉ — the count that fits the
  copy queue into the input dead zone
- slot ceiling = ⌈pool × copy-time ÷ build-time⌉ — BPOs past which BPCs
  arrive faster than slots can build
- the acquisition ladder (un-gate one resource, the next surfaces) is
  manual analysis in TYPHOON-CHAIN.md; automating the iteration is M12 work

## Status and caveats

- Golden values: `chain_expand.py 644 1` and `timeline_model.py 644 100`
  reproduce TYPHOON-CHAIN.md's tables; small-N timeline values differ
  slightly from the doc's charts (the doc used linear-rate approximation,
  the script computes directly — the script is the source of truth).
- Unverified inputs (M4's dogma task): skill→time/copy multipliers,
  whether copying is skill-reducible, reaction slot semantics, exact
  BPO job-lock behavior.
- Known simplifications: serial phases (no pipelining — parked open
  question in MILESTONES.md), one skill multiplier per model run (real
  assignments weight per character), facilities/rigs not yet multiplied
  (M3 data), market pricing absent (M10).
