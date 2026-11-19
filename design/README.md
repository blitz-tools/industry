# Design — build planner mockups

Per-chain wireframe sets under `design/<target>/` — one directory per
simulation target, matching the `reference/chains/<TARGET>-CHAIN.md`
document it visualizes. Shared styles and components live in
`design/shared/` so every set renders identically.

| Directory | Set |
|---|---|
| `typhoon/` | planner → build plan → active plan — the **reference standard** |
| `charon/` | planner → build plan → active plan (capital stress test) |

These are design artifacts for iteration, **not** app code: no build
step, no JS, nothing wired to the FastAPI app. They are deliberately
kept out of `docs/` so the Zensical site never publishes them (they
contain live character and corporation names).

## The mockup convention (binding)

The Typhoon set is the target reference. Every chain gets **the same
pages, layout, components, and visual language — only the data
changes**. Do not invent per-chain visuals or restyle components: a
reader moving between sets should need zero re-orientation. New
components or layout changes are proposed once against the reference
set; once settled they apply to every set (decisions graduate to
`MILESTONES.md` per the flow in `AGENTS.md`).

- Styles come from `../shared/mockups.css` — design tokens and
  component shapes copied from `app/static/style.css`, which remains
  the styling source of truth.
- Dashed yellow `.anno` boxes are wireframe annotations and would
  never ship.
- Data provenance is documented per set in that set's README:
  quantities, phases, and timelines from the matching chain document;
  blueprint ownership from the live `blueprints` table; material
  *availability* numbers may be invented for meter demos and are
  flagged there.
