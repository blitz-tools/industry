# Mockup iteration notes

Working notes for design passes on these mockups. Settled decisions
graduate to `MILESTONES.md` ("Decisions already made") and are removed
here — this document shrinks as it is consumed; it is not an archive.
Line references are point-in-time and drift as files are edited —
locate by feature if a line is stale.

## Original spec (from the prompting session)

Distilled below. If a question ever comes up about exactly what the
original spec said, the full prompt is preserved verbatim in
`ORIGINAL-PROMPT.md` (optional reading — this section is the working
reference).

Two pages: the **build planner** (search → select → target count) and the
**build plan** (the calculated result). Key requirements as specified:

- Search box with autocomplete: all matching blueprints as you type, icon
  beside each match. "Match From Inventory" button filters to owned only.
- After selection: overview of components/materials with required counts,
  updating live as target count changes. Multiple copies of the same
  blueprint shown as an overlay with location, ME, and TE per BPO/BPC.
- "Calculate" at the bottom executes the plan: raw material requirements,
  blueprint copy requirements (BPC count + run counts), job allocation
  overview, and a visual reverse product chain indicator.
- Raw materials list: target count, available count, percentage, and a thin
  horizontal bar (e.g. 5.3M tritanium required, half available → 50% bar).
- Required blueprints listed with Missing / Owned chips.
- Job allocation: characters and their job slots, each slot showing the
  blueprint to use, job type (**reaction, copy, invention, or manufacture**),
  the structure to run it in, and the run count. In-progress jobs show status
  and time-to-delivery. **"Next up" shows *the next job that should be
  executed in this slot* once delivery completes** (definite, singular).
- The product chain is **live-modifiable**: stages can be marked "Purchase"
  via a chip that toggles back to "Build". The spec said "identify build
  *stages* that they want to mark as purchase" — stage-level wording.
- Stage state vocabulary (exactly four, as specified):
  1. **Missing inputs** — materials or components not yet available
  2. **Ready to build** — inputs available AND a job slot is free AND the
     blueprint copy/original is available
  3. **Ready to Deliver** — the jobs satisfying the stage are completed and
     ready to deliver
  4. **Stage Complete** — all outputs delivered from the stage
- No market data (out of scope; pricing is M10).

Implementation notes already settled: blueprint types return 400 on the
plain icon endpoint, so icons use the bp/bpc render variants (matching the
app's `type_icon_url`); all image URLs across the pages verified HTTP 200.

## Review outcome — settled

2026-11-17 pass:

- **"In progress" (cyan) stays as a fifth stage state.** The spec's four
  states jump from "Ready to build" to "Ready to Deliver" with nothing for
  the executing phase. This is a genuine spec gap, now filled.
- **Next-up hints on idle slots stay in the fresh plan too** (extension
  beyond spec, judged more useful than only-after-delivery).
- **`.activity-tag.inv` (invention) stays in the CSS** — invention is a
  spec'd job type; the Typhoon chain simply has no invention nodes.
- Everything else matches spec: Match From Inventory, live target recompute,
  owned-copies overlay, material meters, required-blueprint chips, two-page
  split. No iteration needed there.

2026-11-18 product-owner calls (applied to the mockups same day; the
milestone-affecting vocabulary graduated to `MILESTONES.md`):

- **State model**: the chip carries the spec state; the gating reason
  (BPC copy progress, waiting upstream) renders as secondary text + meter
  beside it. Phase summaries roll up worst-child; purchased nodes drop out
  of phase state/percent and count toward acquisition.
- **Purchase scope**: node-level data model + phase-level bulk toggle
  ("Purchase all" on phase rows and the fresh plan's chain strip).
- **Next-up**: one owner per queued job — queued jobs are labeled per BPC
  ("LSBU BPC 1 × 125 runs" on schlepzrage, "BPC 2" on Octavia); queue
  depth is next + one "then" + a "+N more" count.
- **Blueprint availability is plan-time**: the active page omitting the
  Required blueprints section is the intended behavior — the blueprint
  set is considered immutable once a plan is active. A missing
  blueprint at plan time forces the node to Purchase (chip locked, no
  Build option), and purchasing removes the node's inputs from the
  raw-material math (the commodity itself is acquired instead). →
  graduated to `MILESTONES.md`.
- **Phase numbering**: phases now count up in build order (fuel blocks =
  phase 1 → target = phase 5), so phase and wave numbers increase
  together toward completion — waves are temporal install batches,
  phases are dependency layers, and progress moves both counters the
  same direction. → graduated to `MILESTONES.md`; the reference models
  + `TYPHOON-CHAIN.md` renumber is tracked in `TODO.md`.
- **Copy-vs-direct**: no dedicated UI — the planner accounts for the
  rule in wave composition, and the wave job requests are the surface
  (an early wave requests the copies later phases need; a later wave
  uses the BPO directly where a copy was unnecessary). → graduated to
  `MILESTONES.md`.

Polish bundle applied 2026-11-18: `slot ready` borders on the four fresh
manufacturing slots; sentence-case stage states; standing tint on the
Purchase chip so interactive chips read differently from outline-only
state pills; job splits in `node-runs` in both views; copy-plan no-copy
rows moved to a footnote with best-ME wording ("10 runs from the best-ME
BPCs, ME 10 / TE 20"); acquisition table defaults to gaps only with a
"Show all 29 types" toggle and a "blocks CTR builds" callout on Chiral
Structures; required blueprints collapsed to a summary line plus
exceptions (Typhoon BPC-only, off-location Hydrogen BPO).

Also fixed while in there: the fresh plan's "25 types" stat tile — the
`TYPHOON-CHAIN.md` terminator table has 29 types (7 minerals + 4 moon +
10 PI + 8 ice), so the tile now reads 29.

## Open

Nothing open — every decision from the 2026-11-17 review is settled and
graduated. New findings from the next design pass start here.
