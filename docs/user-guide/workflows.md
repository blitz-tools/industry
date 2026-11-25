# Build workflows

The intended workflows end-to-end: how a build goes from a search box
to a saved plan of record, and why the pieces fit the way they do.
Each step names the control it uses, and a screenshot pass will add
figures with the active controls highlighted as the surfaces
stabilize — one figure slot per section below.

The short version: **everything is set before Calculate, nothing is
edited after Render.** The planner is a planning surface; the saved plan
is a document. Changes to a saved plan are either a marking (a small,
in-place amendment) or a re-plan (a new plan) — never an edit of the
calculation itself.

## Plan a build

Start at **Industry → Planner**.

1. **Find a target** — search the buildable catalog by name. The
   results badge each product with blueprint ownership from the live
   syncs. *Match From Inventory* narrows the list to what the
   corporation can already build from owned blueprints.

2. **Set the target count** — the stepper beside the target accepts
   +/− clicks or a typed number (press Enter). Quantities are
   planning-phase inputs: the count rounds up to whole runs and jobs
   everywhere downstream, so it is set here, once.

3. **Plan participants** — who the plan may assign work to. The main
   character's corporation scopes the default pool (every member in);
   other-corporation characters are included per plan and need a
   distribution step before their jobs can install. Skill gates and
   per-character time multipliers resolve against this pool.

4. **Plan facilities** — where each activity runs. The Structures
   registry supplies one default per activity; the planner can
   override per plan without touching the registry. Every number the
   plan shows multiplies against these: material requirements (ME
   rig), job durations (TE rig + hull), install cost (system cost
   index × facility tax).

5. **Material sources** — where the stock meters count from. The
   default is every corp office hangar and container in them;
   personal hangars opt in per character per location. Narrowing to
   the local build system is the normal move — the acquisition table
   shows where stock sits either way, so what is not in place is
   visible as a move.

6. **Calculate** — resolves the full chain: phases from raw
   terminators to the target, per-node runs and jobs, the stage states
   (ready / missing inputs, with the gating reason), blueprint
   coverage, install cost, per-participant time, and the raw-material
   acquisition table with coverage meters.

> **Figure — planner.target** *(pending the screenshot pass)*: the
> Target build card with the count stepper and the Calculate bar
> highlighted.

## Render the plan

The **Render plan** button (▤, green highlight) on the calculated page
snapshots the resolved chain as a new plan of record: participants,
facilities, material sources, every node's quantities and calculation,
and the acquisition lines, all pinned at export. Roster changes,
registry edits, and stock movements never move a saved plan — the
snapshot is what was true at save time.

The plan starts as a **draft**. It activates when its first job
installs (or when activated manually), and completes when every node
is satisfied — build nodes delivered, purchased nodes in the pool.

> **Figure — plan.save** *(pending the screenshot pass)*: the
> calculated page's header with the Render plan button highlighted.

## Work with saved plans

**Industry → Plans** lists every plan with its pool, status, and
snapshot counts, and manages them in bulk: select any rows (the header
checkbox selects all) and **Activate** the drafts, **Deactivate** the
active plans, **Abandon** the drafts and active plans (confirm
dialog), or **Delete** the abandoned plans (permanent — confirm
dialog; the snapshot rows go with the plan). Each action applies to
the applicable part of the selection, so mixed selections are safe.
The detail page is the read-only plan of record.

Two buttons change the plan's shape, and they answer different
questions:

- **Copy plan** (⧉, blue) — the same chain back on the calculated
  page, with the same context and no strings attached. Adjust the
  material sources (the common case: the same build fed from a
  different container or hangar) and save — a new, **concurrent**
  plan. The source plan is untouched. This is also the front door for
  running the same build repeatedly on a cadence (the plan-of-plans
  stacking idea: the same weekly deliverable planned four times over a
  month).

- **Branch plan** (⎇, yellow) — the same planning setup back on the
  planner **entry**, with nothing pinned to the outcome: adjust the
  target, count, participants, facilities, or sources, then save as a
  new **sibling** plan. A branch diverges from its origin and keeps it
  — nothing is abandoned, and both plans run concurrently.

- **Re-plan** (⟳, purple) — all the way back to the planner **entry**,
  with the plan's state loaded. The target, count, participants,
  facilities, and sources are all adjustable there, because a re-plan
  is planning again, not editing: the target and count are
  planning-phase inputs, and changing them recomputes the whole chain.
  Rendering from a re-plan **supersedes** the source plan: the old one is
  marked abandoned and points at its replacement, so the history reads
  as a line of succession rather than a pile of near-duplicates.

## Mark Purchase⇄Build

Every node row on the plan detail carries a **Build** / **Purchase**
chip, and every phase summary a **Purchase all** / **Build all**
toggle. Marking is the one in-place amendment a saved plan allows:
a purchased node drops out of phase progress and tracks the pool
instead (it is satisfied when the commodity actually sits in the
plan's material sources), and everything only it consumed turns
**unnecessary** — greyed out in the phase tree and the reverse-chain
strip, its raw-material demands gone from the acquisition table. The
purchased commodity itself joins that table as a purchase line.

Two rules keep the math honest:

- The amendment recomputes from the snapshot, so un-marking is
  symmetric — demands return exactly as they were.
- Suppliers **shared** with still-built nodes keep their full planned
  quantities in v1: purchasing an intermediate never shrinks a
  shared parent's requirement (re-deriving a chain around a local
  change is the wave model's job, M9 — never a local patch). Dead
  suppliers — the ones nothing still-built consumes — drop out
  entirely.

A node whose blueprint the pool no longer holds locks to **Purchase**
(the chip is disabled) — the gate re-derives as the pool changes, and
**Purchase all** still marks locked nodes. Marking a chip keeps the
page in place: the viewport does not move, and the phase tree keeps
its expanded/collapsed state.

## Export the shopping list

The **Export plan** button (↗) on the plan header opens the multibuy
shopping list in an overlay: the whole list in a large fixed-width
text box, one `Item Name<TAB>Quantity` line per short acquisition row
— raw gaps against the marking-amended requirement plus purchase
lines — sorted by name. **Copy** puts it on the clipboard for the
in-game multibuy window. (Without scripting, the same button
downloads the list as a `.txt` file.)

## Watch progress

Once saved, a plan tracks itself. A background refresh re-measures
material availability against the plan's pinned sources, matches the
corporation's synced industry jobs to plan nodes (by blueprint,
activity, and facility location), and rolls delivery forward from the
jobs' completed runs — no page load ever waits on ESI.

Jobs install in-game as usual; nothing needs to be filed anywhere.
When a job's blueprint matches a node, it shows on that node —
installer, runs, and time to delivery — and the node moves through
**In progress** and **Ready to deliver** to **Stage complete**. The
matching is a heuristic: a job started before the plan was exported
never matches, and one job claims into at most one plan (the oldest).
**Activate** forces a draft active when the matcher missed its jobs —
the counterweight to a heuristic; **Deactivate** pulls an active plan
back to draft (the escape hatch when a false positive flipped it
early — it stays draft while its jobs still correlate, until activated
again); **Abandon** closes a plan (terminal — its jobs free up for
other plans). A plan completes on its own when every node is
satisfied: build nodes delivered, purchased nodes with the commodity
sitting in the pool.

> **Figure — plans.progress** *(pending the screenshot pass)*: a plan
> detail with an In-progress node carrying its matched job, and the
> plans list's progress column.

> **Figure — plans.actions** *(pending the screenshot pass)*: a plan
> detail header with the Copy plan, Branch plan, and Re-plan buttons
> highlighted.
