# Mockup iteration notes — 2026-11-17

Working notes for the next design pass on these mockups. Captures the review
of all three pages plus `mockups.css`, the decisions already made, and the
recommendations still awaiting a product-owner call. Line references are
point-in-time (2026-11-17) and will drift as files are edited — locate by
feature if the line is stale.

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

## Recommendations awaiting product-owner decision

1. **State model (highest value — changes what M5/M6 encode).** The active
   view shows `Copying BPC 1/3 · 19%` on phase 1 nodes in the same cyan
   `running` state used for phase 3 nodes whose own jobs execute. Per spec
   those phase 1 nodes are **Missing inputs** (blueprint not yet available),
   and that's why the phase 1 summary doesn't roll up from its children.
   Proposed fix: the state chip carries the spec state; the gating detail
   becomes secondary text + meter beside it
   (`Missing inputs` + `BPC copy 19% · ready day 8.3`). Phase summaries then
   derive from children by a roll-up rule (worst/limiting child state).
   Purchased nodes drop out of the phase state and percent, counting toward
   the acquisition side instead.
2. **Purchase chip scope.** Spec said stage-level; mockups went node-level
   (deliberate deviation). Proposed reconciliation: node-level as the data
   model (purchase decisions are per-commodity; phase-level storage forces
   all-or-nothing on M5 resolution), plus a phase-level bulk toggle that sets
   all child chips — recovering the spec's stage ergonomics.
3. **Next-up assignment semantics.** Spec is definite ("the next job that
   should be executed in this slot"), but the fresh plan shows
   `LSBU ×125 runs — waiting on BPC (day 4.2)` queued on both schlepzrage
   and Octavia. Fix: assign each queued job to one character. Also define
   the display rule for how many queued jobs a slot group shows (fresh plan
   hints one reaction per character; the active view runs four per
   character).

## Polish bundle (apply without discussion)

- Fresh plan: the four ready manufacturing slots lack the `slot ready` class
  the AIPS copy slot has (green border missing; state conveyed only by
  inline-styled green text).
- Stage-state capitalization drift: `Ready to build` / `Ready to Deliver` /
  `In progress` / `Missing inputs` — standardize on sentence case.
- `.stage-chip` and `.stage-state` are both 999px pills; Purchase chip is
  outline-only like the states while Build has a 15% tint. Give Purchase a
  tint (or fill states) so interactive chips read differently from
  informational states.
- `node-runs` shows `30 runs` in the fresh view but `30 runs · 3 jobs` in
  the active view — show the job split in both.
- Copy plan: `covered by owned BPCs (9 + 1 runs)` is unexplained next to
  "10 BPCs / 52 runs total in pool" — reword to best-ME selection, e.g.
  `10 runs from best-ME BPCs (ME 10 / TE 20)`, or add an anno.
- Copy plan: move the two no-copy rows (Typhoon, fuel blocks) to a footnote;
  they're noise in a "what to copy" table.
- Acquisition table: most of the 25 rows are 100% covered. Default to
  "show only gaps" (or collapse covered groups) so blockers like
  `Chiral Structures 0% — blocks CTR builds` stand out.
- Required blueprints: when everything is owned, a summary line plus
  exceptions beats 15 green rows.
- Confirm whether the active page omitting the Required blueprints section
  is intentional (it's the "abbreviated to what moved" reading).
- `.badge.bpo` and `.badge.owned` are byte-identical styling — fine
  semantically, noted only so a future consolidation isn't a surprise.
- A11y for the real app (fine in wireframes): `.stage-chip` is a
  `cursor: pointer` span — ship as `<button>`; autocomplete rows need
  keyboard navigation.

## Suggested order

1. State model (recommendation 1) — settles M5/M6 vocabulary.
2. Next-up semantics (recommendation 3) — M9 orchestration data.
3. Purchase interaction (recommendation 2).
4. Polish bundle — one pass over all three pages.
