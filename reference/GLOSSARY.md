# Glossary — math and model terms

Lookup reference for the symbols and terms used in the chain documents
(`reference/chains/`) and the formula reference (`reference/README.md`).
By decision (2026-11-18) these stay **unexpanded in the documents** —
this file is the lookup. EVE commodity abbreviations (AIPS, LSBU, CTR,
RCF, …) follow the opposite rule: expanded at first reference per
document as SHORT (expansion).

## Chain structure

| Term | Meaning |
|---|---|
| **N** | Target count — the number of final targets the plan builds. All quantities are linear in N, so ratios never move with scale. |
| **phase** | Dependency layer of the resolved chain, counted **up in build order**: raw-material terminators sit at phase 0, the deepest buildable layer is phase 1, the target is the highest number. A node's phase = 1 + max(its inputs' phases). |
| **terminator / raw** | A type with no producing blueprint (minerals, moon materials, PI commodities, ice products). Leaf of the chain — acquired, never planned through. |
| **products-per-run** | SDE `industryActivityProducts.quantity` — units one run yields (components 3/run, fuel blocks 40/run). |
| **R** (runs) | ⌈units ÷ products-per-run⌉ — runs needed for a commodity. |
| **aggregation** | Same-type requirements merge per phase and round runs once — not per parent branch — which is where run-count savings come from (RCF 8 per-branch → 7 aggregated). |

## Jobs and slots

| Term | Meaning |
|---|---|
| **pool** | Total build slots across characters for one activity (characters × 10 at max skills). |
| **k** | Runs per job: min(maxProductionLimit, ⌈runs ÷ pool⌉) — job sizing that fills the pool without exceeding the blueprint ceiling. |
| **jobs** | ⌈runs ÷ k⌉ — how many parallel jobs a commodity splits into. |
| **even split** | Job run counts kept within one run of each other so all jobs end together (deliver-together objective). |
| **wave** | Install batch at a login window — what starts together, membership by eligibility (inputs ready, slot free, blueprint available). Also a slot-concurrency batch within a phase (commodities share slots sequentially in waves). |
| **WINDOW** | Login-window length in hours; 6 h in the proof-outs. A plan parameter, not a constant. |
| **maxProductionLimit** | SDE per-blueprint ceiling on one job's run count (Typhoon 10, CTR 40, components/fuel blocks 200). |
| **blueprint job-lock** | One active job per blueprint (original or copy) — concurrency per commodity is min(pool, blueprint count), never slots alone. |

## Times

| Term | Meaning |
|---|---|
| **t_base** | Base build time per run, from SDE activity 1, before skills. |
| **t_b** | Skilled build time per run = t_base × the runner's skill multiplier. |
| **t_c** | Copy time per run, from SDE activity 5. |
| **skill multiplier** | Per character, from Industry × Advanced Industry (mapping pending dogma verification; 0.68 is the max-skills scenario, never a global constant). |

## Scheduling

| Term | Meaning |
|---|---|
| **T_in** | Input-ready time — when a phase's inputs exist: the scheduled end of the next deeper phase. The dead zone ends at T_in. |
| **dead zone** | The gap before a phase can start — inputs not yet built, or BPCs not yet copied. |
| **dead wait** | The copy-overflow segment specifically (the "BUILDS WAIT" rows): T_in → copy-queue end, caused by the copy queue overrunning the dead zone. |
| **chain end** | Total wall-clock days for the whole chain, start to final delivery. |
| **d/N** | Chain rate — days per target unit. |
| **copy queue** | R·t_c — total copy hours for a commodity's BPCs, sequential per BPO. |
| **copy÷T_in** | Queue ÷ dead-zone ratio. Above 1 means the copy queue overflows into dead wait; 1.56 for AIPS at every N. |
| **strategies** | `copy` (pure copy), `hybrid` (copy the longest queue until T_in, then build direct), `2bpo` (a second BPO halves the longest queue). |

## Copy-vs-direct rule

| Term | Meaning |
|---|---|
| **break-even multiplier** | t_c ÷ t_base (≈ 0.8 for the T1 components). A character should switch from copying to direct building when their skill multiplier drops below it. |
| **the rule** | Copy while input-starved (the queue monetizes BPO dead time); build direct once inputs flow, if t_b < t_c. Low-skill characters keep copying; max-skill characters switch. |

## BPO obtainment (M12)

| Term | Meaning |
|---|---|
| **queue rate** | Copy hours per target unit (copy queue ÷ N) — scale-invariant. |
| **input-ready rate** | T_in growth per target unit (days per unit, linear in N). |
| **min BPOs** | ⌈queue rate ÷ input-ready rate⌉ — the count that fits the copy queue into the input dead zone. |
| **slot ceiling** | ⌈pool × t_c ÷ t_b⌉ — BPOs past which BPCs arrive faster than slots can build them; extras idle. |
| **trigger count** | The N where queue(N) = T_in(N) — below it one BPO suffices, above it the queue overflows. |

## Purchase economics

| Term | Meaning |
|---|---|
| **procurement lead** | Wall-clock time to acquire a purchased commodity (market/contract). |
| **purchase crossover** | Purchasing a node wins on wall time whenever procurement lead < copy-queue overflow + build time. Whether to pay is the profit-vs-throughput slider's job, not the math's. |
| **seesaw** | An upstream purchase shrinks T_in, evaporating the dead zone that makes copying free — purchases can flip downstream copy-vs-direct verdicts, so every Purchase ⇄ Build toggle is a full re-derivation. |
