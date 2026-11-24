# Whole-catalog census — findings

The recorded output of whole-catalog analysis over the SDE mirror
(release 2026-11-20, run 2026-11-21). The first census pass covered
**phase depth** and **cycle detection** — the two structural
properties the chain program's ten walked chains could only
sample. This document holds the expanded findings; the
[`README.md`](README.md) model notes carry the compressed
versions. The full `--all` census (multi-producer types,
unclassified terminators, walk failures) is the M5 validation tool
recorded in TODO.md — findings from it land here too.

## Phase depth is bounded at 7 by the SDE

The deepest possible target sits at **phase 7** (8 levels counting
the phase-0 raw tier). Every chain the program walked — Typhoon
through Ragnarok — caps at phase 6, and that is not a coincidence
of target selection: phase 6 is the ceiling of the
capital-component world (raw → fuel block → simple reaction →
advanced reaction → component → capital component → capital ship).
One more level exists, created by a single mechanic:

**Ship-on-ship nesting at capital scale** — the "T1 hull as build
input" mechanic the Panther chain documented (the Typhoon nests
inside the Panther), applied one size class up. The 29 depth-7
products:

| Group | Count | The nesting |
|---|---:|---|
| Jump Freighters | 4 | Ark → Providence (each nests its racial freighter) |
| Command Carriers | 4 | Ymir → Nidhoggur · Gaia / Simurgh / Salvation → their racial carriers |
| Lancer Dreadnoughts | 4 | Valravn → racial dreadnought · Karura / Bane / Hubris (the EDENCOM class) |
| Faction-edition Dreadnoughts | 4 | Naglfar Justice Edition → Naglfar · Revelation Sarum · Phoenix Wiyrkomi · Moros Interbus |
| Faction-edition Marauders | 12 | Vargur Nefantar Edition → Vargur → battleship · the Golem / Kronos / Paladin edition families |
| Capital Industrial Ship | 1 | Rorqual ORE Development Edition → Rorqual |

The canonical deepest backbone (8 levels):

```text
raw PI → fuel block → Carbon Polymers (simple reaction) →
Pressurized Oxidizers (advanced reaction) → Core Temperature
Regulator (component) → Capital Core Temperature Regulator
(capital component) → Nidhoggur (capital ship) → Ymir (command
carrier)
```

Every depth-7 path runs through that same component spine — the
extra level is always a capital ship consumed as a build input.

**Depth histogram** (5,014 buildable products; the 2026-11-24
regeneration via `chain_expand.py --all`):

| Depth | Products | What lives there |
|---:|---:|---|
| 7 | 29 | the ship-on-ship nesters above |
| 6 | 240 | capitals · supercapitals · titans · T2 battleships · navy capitals · control towers · the deep module world |
| 5 | 778 | battleships · cruisers · T2 cruisers · faction towers · most ships |
| 4 | 398 | frigates · destroyers · T2/T3 frigates · drones · deeper modules |
| 3 | 156 | components with component inputs · charges with intermediates |
| 2 | 801 | reactions · fuel blocks · intermediates |
| 1 | 2,612 | direct-from-raw builds — most of the module/charge/drone world |
| 0 | — | (raw terminators are not counted as products) |

(2026-11-24 correction: the original run's mid-depth buckets came from
an uncommitted session script; the committed `--all` tool — walking
with the M5 rule, producers restricted to activities 1 and 11 — puts
the bulk of the catalog at depth 1, which an independent SQL check
confirms. The headline findings are unchanged: the ceiling, the 29
nesters, the cycle count.)

**Consequences**:

- Every chain set the program walked sits one phase under the
  catalog's ceiling. A jump-freighter or command-carrier set
  (chain or mockup) would touch phase 7 — the only unwalked
  structural level, and it adds no new mechanic (it is the
  Panther's nesting at capital scale), so the models are not
  missing anything by not having walked it.
- The planner's phase view should not assume a depth ceiling; M5
  renders whatever the walk produces. The practical bound (7)
  matters for UI stress-testing (the phase tree's collapse
  behavior at 8+ levels) and for the M9 wave model (nothing
  structurally new appears below phase 6).

## The cycle assumption is wrong — 51 cycles exist

The reference model's note "cycle detection: NOT implemented (T1
manufacturing has none)" is disproven by the census: **the SDE's
mfg+reaction producer graph contains 51 cycles**, and the census's
first run hit infinite recursion because of them. The cycles are
almost entirely **self-referential structure arrays** — the
Component Assembly Array lists 1× *itself* as a build input
(typeID 24660, material list `[(Component Assembly Array, 1)]`);
the same pattern covers the Design Laboratory, Capital Ship
Assembly Array, Simple Reactor Array, and the rest of the
starbase-structure family, plus a handful of orbital munitions.

**Consequences**:

- M5's defensive cycle-detection mandate is **provably
  necessary**, not merely prudent: a naive resolver would
  infinite-loop on any structure-targeted plan (the M3 structure
  manager's own subject matter).
- The walk's `producers()` first-row choice never enters a cycle
  on the chains the program walked (no chain set targeted a
  starbase structure), so the reference outputs are unaffected —
  but the resolver M5 ships must detect and break cycles
  explicitly (treat the back-edge as terminal, as this census
  did) and surface them rather than silently truncating.
- The cycles appear to be SDE data quirks (self-inputs in
  structure bills) rather than real game mechanics — a structure
  that genuinely required itself to build would be unobtainable.
  Worth a pin: verify whether the live game's structure bills
  match the SDE here (an SDE-export artifact vs. a real
  self-reference).

## Method

Both findings come from a single-pass memoized walk over the
5,014 products of activities 1 and 11, with path-tracking to detect
cycles (back-edges treated as terminal and recorded). The walk is now
committed as `chain_expand.py --all` (landed with M5, 2026-11-24): it
uses the prefer-published producer rule the app catalog resolves with,
restricted to the walk activities (1 and 11). Regenerate with
`podman exec industry_dev_1 python reference/chain_expand.py --all`;
the numbers here are pinned to the 2026-11-20 SDE release as
re-generated 2026-11-24. The app-side counterpart
(`tests/functional/test_chain_sde.py`) proves the resolver against
this census every catalog-proof run: every product resolves, cyclic
membership matches, and cut-free chains match the memoized depth.
