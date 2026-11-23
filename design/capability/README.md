# Capability mockup — the M12 surface

The last of the three surface mockups (after structures and
markets): "what should we build" — the fork-point substrate both
M13 (train) and M14 (farm out) consume, and the input the end-goal
loop closes on. The match joins synced skills and owned blueprints
against the buildable catalog, lazily per target on demand — never
by pre-expanding the catalog's chains.

| File | Shows |
|---|---|
| `capability.html` | Pool + market scope pickers, the ranked end-products table (fixed buildability grouping — producible / partial / blocked — with the **composed sort selector**: Fewest gaps active, Est. margin staged-disabled until M15), the per-target gap report (node / gap badge / detail / remedy-link rows — acquire, train, farm), the BPO obtainment ladder ("this BPO buys N days"), and the LP portfolio input card |

## Design positions (flagged in `.anno` boxes on the page)

- **The composed selector** (2026-11-22 direction): buildability
  grouping is fixed; the chip pair selects the within-group sort.
  The margin option renders disabled with the not-yet-present badge
  until M15's price sync — the staged-state treatment, visible from
  day one.
- **Gap counts are fields per gap type** (skills / blueprints /
  LP / facility), never composed sentences — any scenario is a
  badge and a count.
- **Every gap type carries its remediation link** — Acquire (the
  BPO ladder), Train (M13), Farm (M14): the fork made clickable.
  Skill rows hold the no-holder and underleveled-holder states from
  the chain program (the Hel's CSC 1 → 4 is the worked example).
- **Acquire opens an acquisition-detail panel, never a
  transaction**: path-specific matched listings from the synced
  tables (contract matches with runs/ME/TE, NPC-market orders for
  seeded formulas, LP store offers with the shortfall), the
  alternatives (buy-the-commodity at M15 prices; a BPO original
  with its ladder days-saved when a rung exists), and **one action:
  Open in planner** — pre-calculation purchase intent is rejected
  (2026-11-18), so capability shows what it would take and the plan
  is where the decision lands. The panel is shown expanded on the
  Charon Blueprint row as the demo state.
- **The LP portfolio is an input, not an error** — wrong-currency
  wealth reads as its own gap type (the TFI set's persisted view,
  promoted).
- All conventions baked in from the start: `.var` marking (spans
  only; tables/badges dynamic-by-construction), no
  scenario-composed sentences, state badges + fields + static help.

## Data provenance

- Real: the ten chain targets' buildability positions and gap
  counts (the chain program's recorded facts — Charon's 18 missing
  blueprints, Panther's 33, Hel's 35 + the facility gap, the
  underleveled CSC holder, the pool-relative Rage/Panther
  footnotes); the LP portfolio balances (live-synced); the Charon
  Blueprint contract listing (the real The Forge find); the
  5,014-product buildable catalog count (the census).
- Illustrative: BPO ladder costs and days-saved (the closed-form
  math is recorded; the figures await M10/M15), all margin figures
  (absent by design — the M15 badge).

## Milestone mapping

| Mockup section | Milestone |
|---|---|
| Catalog-wide capability match, ranked products | M12 |
| Per-target gap report (fork substrate) | M12 → M13 / M14 |
| BPO obtainment ladder | M12 (rules in TYPHOON-CHAIN.md) |
| LP portfolio input | M12 (from the TFI set) |
| Margin sort staged-disabled | M10 over M15 |
