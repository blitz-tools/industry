# Build workflows

The intended workflows end-to-end: how a build goes from a search box
to a saved plan of record, and why the pieces fit the way they do.
Each step names the control it uses, and a screenshot pass will add
figures with the active controls highlighted as the surfaces
stabilize — one figure slot per section below.

The short version: **everything is set before Calculate, nothing is
edited after Save.** The planner is a planning surface; the saved plan
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

## Save the plan

The **Save plan** button (⭳, green highlight) on the calculated page
snapshots the resolved chain as a new plan of record: participants,
facilities, material sources, every node's quantities and calculation,
and the acquisition lines, all pinned at export. Roster changes,
registry edits, and stock movements never move a saved plan — the
snapshot is what was true at save time.

The plan starts as a **draft**. It activates when its first job
installs (or when activated manually), and completes when every node
is delivered.

> **Figure — plan.save** *(pending the screenshot pass)*: the
> calculated page's header with the Save plan button highlighted.

## Work with saved plans

**Industry → Plans** lists every plan with its pool, status, and
snapshot counts. The detail page is the read-only plan of record.

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
  Saving from a re-plan **supersedes** the source plan: the old one is
  marked abandoned and points at its replacement, so the history reads
  as a line of succession rather than a pile of near-duplicates.

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
the counterweight to a heuristic; **Abandon** closes a plan (terminal
— its jobs free up for other plans). A plan completes on its own when
every node is delivered.

> **Figure — plans.progress** *(pending the screenshot pass)*: a plan
> detail with an In-progress node carrying its matched job, and the
> plans list's progress column.

> **Figure — plans.actions** *(pending the screenshot pass)*: a plan
> detail header with the Copy plan, Branch plan, and Re-plan buttons
> highlighted.
