# Markets mockup — the M15 sync panel surface

The second of the three surface mockups (after M3's structures
page): the market manager plus its world-state observability subset,
proposed once against the reference component set. It is the
**market manager** the 2026-11-22 direction shaped — sibling
registry to the Structures page, feeding the planner's sell-side
market selector the same way the facilities section reads the
structure registry. Division of record: **industry facilities in
the structure manager, markets here**.

| File | Shows |
|---|---|
| `markets.html` | Market sources (the five trade hubs default-and-disableable, the player market with its scope-prerequisite state, edit/delete on customs), the add-market form (region type-ahead + player-structure search), sync families (per-family cadence / freshness / rows), and the rate-limit headroom gate — meters plus **per-candidate expansion rows** (estimate field + gate-state badge) with static help text |

## Design positions (flagged in `.anno` boxes on the page)

- **Disabled hubs are the gate's decision, not missing
  configuration** — the headroom card is the same number the sync
  loop checks before expanding, rendered wherever the hub list is.
- **Scope-prerequisite state, not errors** — the 5 Times player
  market shows "scope needed" (`esi-markets.structure_markets.v1`
  unregistered, live fact); its public contracts arrive via the
  Metropolis region scan regardless.
- **The Observability subset rule** — this page's families and
  headroom are page-filtered views of the one stored dataset; Admin
  > Observability holds the central view, and the checks are never
  duplicated (2026-11-22 direction, TODO.md).
- **Adding a disabled hub is allowed** — lists immediately, syncing
  starts when headroom gates it in; re-adding a seeded hub is an
  idempotent no-op.
- **The LP store offers family sits outside the ESI rate-limit
  budget** — fuzzwork lpstore dataset, so it never appears in the
  headroom meters.
- **No scenario-composed sentences** (2026-11-22 direction): the
  headroom gate renders as candidate rows — estimate field + gate
  state badge — with levers and standing requirement as static help
  and the remediation as a link. Any scenario is a badge and two
  fields. This page is the pattern's reference implementation; the
  same sweep normalized the chain sets' active market readouts (drift
  and next-re-check as slots) and settled lines (fixed-slot ledger
  entries with note fields).

## Data provenance

- Real: the five hub regions and their IDs (The Forge 10000002,
  Domain 10000043, Heimatar 10000048, Metropolis 10000052, Sinq
  Laison 10000037); the 5 Times Nearly Winners Keepstar; the
  unregistered scope prerequisite; the fuzzwork lpstore dataset
  counts (31,952 offers across 181 stores); the staged-rollout and
  family-order decisions from MILESTONES.
- **Illustrative**: sync timestamps, cadences, row counts, and
  rate-limit percentages — the budget math lands with
  implementation; the standing requirement the panel serves (the
  app never rides its rate limits) is recorded in M15.

## Milestone mapping

| Mockup section | Milestone |
|---|---|
| Market sources, add market | M15 sync_hubs (the market manager) |
| Sync families status | M15 framework slice |
| Rate-limit headroom gate | M15 staged rollout |
| Observability subset rule | Admin > Observability (TODO) |
| LP store offers family | M15 LP store offers (fuzzwork dataset) |
| Scope-prerequisite state | Player-structure markets (M15) |
