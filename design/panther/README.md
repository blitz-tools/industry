# Panther mockup set

The invention set — same pages, layout, and components as the
reference standard ([`../typhoon/`](../typhoon/README.md), see
[`../README.md`](../README.md) for the binding convention), populated
with the Panther ×1 chain. It exercises what no previous set could:
the **invention input tier** on the planner (source-BPC → invented-BPC,
kept simple per the M8 decision), the **invention plan** on the
calculated build plan (batch size, decryptor choice, confidence), the
**parallel-branch story** (invention jobs batched into wave 1 next to
the fuel blocks), the **three blueprint-acquisition paths** (invented /
NPC-seeded originals / cheap formulas), and T2 components at 1/run
volumes.

| File | Shows |
|---|---|
| `planner.html` | Search (invention source in the autocomplete sub-line), target with the invention-inputs tier (source BPC, datacores vs stock, decryptor pointer), 48-blueprint three-path tier, intermediates and raw summaries, invention-summary card (recipe, 22%, confidence, sole-inventor gate), Calculate |
| `planner-scoped.html` | The unresolvable scenario: participant pool scoped to corp members — no eligible inventor (blitzrage is out-of-corp), the invention path breaks with "no eligible character" gating (distinct from blueprint-missing), the contract-purchase fallback with an honest empty result, and remediation actions (include blitzrage, adding the distribution step) |
| `build-plan.html` | Freshly calculated plan: wave bar with the invention batch as W1 (2.2 d of a 16.0 d chain), 6-phase reverse chain with the T1 hull riding at phase 5, the invention plan (10 attempts · Process decryptor · ME_eff −1 · 92%, with the out-of-corp distribution step for blitzrage's materials), required blueprints across three acquisition paths, Typhoon-world copy plan, gaps-only acquisition with the NPC-market-goods category, wave-1 allocation with all ten of blitzrage's science slots on invention |
| `build-plan-active.html` | The same plan mid-flight (day 6.5 of 16.0): invention complete at 2/10 successes (E = 2.2, actuals-against-expectation framing), two ≈5.5-day T2 component jobs running at 9%, the invented BPC waiting in the hangar, CJD delivered on Octavia |

## Data provenance

- Quantities, phases, runs, and the invention layer come from
  `reference/chains/PANTHER-CHAIN.md` (the model runs at ×1 against
  the live SDE mirror). Invention probability (22%), recipe, and
  durations are SDE data; decryptor modifiers are pinned from live ESI
  dogma (2026-11-19); invented-BPC base ME/TE (−4/−4) is the flagged
  community-documented assumption.
- Blueprint ownership from the live `blueprints` table, pulled
  2026-11-19: 48 blueprints in the chain — the Panther, nine
  NPC-seeded manufacturing BPOs (7 T2 components, Capital Jump Drive,
  R.A.M.), and 23 reaction formulas are genuinely missing (33); the
  Typhoon world (BPCs ×10, AIPS/LSBU/CTR, fuel blocks, R4 formulas)
  is genuinely owned (15). Datacore stock (53 + 11) and the decryptor
  collection (all 8 types, 125 units) are real.
- Skill check real: only **blitzrage** (character 1634367930) holds
  the three invention skills (4 / 4 / 1) — invention jobs serialize
  onto one character; the mockups feature blitzrage for the first
  time. **Corp membership is real too**: blitzrage is out-of-corp
  (1413715023, vs the main's blitz and blitz holdings 98830898) — the
  scoped-pool variant is the actual default for a corp-members-only
  Panther plan, and the standard plan's distribution step (materials
  contracted to blitzrage) is the real cost of using the only
  inventor.
- Wave decomposition (W1 invention batch 2.2 d … W4 ship build), the
  16.0 d chain end, material *availability* numbers, and
  market-average figures are **invented for the wireframe** — anchored
  to the chain document's durations but illustrative in between; the
  real waves are the M9 scheduler's output.
