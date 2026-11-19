#!/usr/bin/env python3
"""Chain expansion reference: per-branch tree, aggregated phases, raw totals.

Executable spec for M5's chain resolution (MILESTONES.md) and the generator
of reference/chains/TYPHOON-CHAIN.md's golden values. Read-only against
the SDE mirror; run inside the dev container from the repo root:

    podman exec industry_dev_1 python reference/chain_expand.py 644 1

Pinned by the 2026-11 proof-outs:

- A type's producing blueprint is its first `industryActivityProducts` row
  (manufacturing = activity 1, reactions = activity 11 in the fuzzwork dump;
  `ramActivities` labels reactions as 9, but the data lives on 11).
- Terminators are types with no producing blueprint. The raw-category lists
  below are hardcoded to the Typhoon chain; M5 should classify through
  invGroups/invCategories instead.
- Cycle detection is NOT implemented here (the manufacturing chain has none);
  M5's resolver must add it defensively per the milestone scope.
"""

import math
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "industry.db"

ACTIVITY_LABELS = {1: "manufacturing", 5: "copying", 11: "reaction"}

# Hardcoded to the Typhoon chain — see module docstring.
RAW_CATEGORIES = {
    "minerals": [
        "Tritanium", "Pyerite", "Mexallon", "Isogen",
        "Nocxium", "Zydrine", "Megacyte",
    ],
    "moon materials": [
        "Hydrocarbons", "Silicates", "Atmospheric Gases", "Evaporite Deposits",
    ],
    "PI commodities": [
        "Chiral Structures", "Water", "Test Cultures", "Viral Agent",
        "Supertensile Plastics", "Nanites", "Robotics", "Enriched Uranium",
        "Mechanical Parts", "Coolant",
    ],
    "ice products": [
        "Strontium Clathrates", "Oxygen", "Heavy Water", "Liquid Ozone",
        "Helium Isotopes", "Nitrogen Isotopes", "Oxygen Isotopes",
        "Hydrogen Isotopes",
    ],
}


def connect():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def type_name(db, type_id):
    return db.execute(
        "SELECT typeName FROM sde_invTypes WHERE typeID=?", (type_id,)
    ).fetchone()[0]


def producers(db, type_id):
    """[(blueprint_type_id, activity_id, products_per_run)] — empty if raw."""
    return db.execute(
        "SELECT typeID, activityID, quantity"
        " FROM sde_industryActivityProducts WHERE productTypeID=?",
        (type_id,),
    ).fetchall()


def inputs(db, bp_type_id, activity):
    """[(material_type_id, quantity_per_run)] for one blueprint activity."""
    return db.execute(
        "SELECT materialTypeID, quantity"
        " FROM sde_industryActivityMaterials"
        " WHERE typeID=? AND activityID=?",
        (bp_type_id, activity),
    ).fetchall()


def runs_for(quantity, products_per_run):
    """Run math: required units divided by the recipe's products per run."""
    return math.ceil(quantity / products_per_run)


def per_branch_tree(db, type_id, quantity):
    """Recipe view: every branch, shared intermediates repeated per parent."""
    lines = []

    def expand(t, qty, depth):
        prod = producers(db, t)
        nm = type_name(db, t)
        if not prod:
            lines.append("  " * depth + f"- {nm} x{qty:,}  [raw]")
            return
        bp, act, per_run = prod[0]
        runs = runs_for(qty, per_run)
        label = ACTIVITY_LABELS.get(act, f"activity {act}")
        note = f" ({runs:,} runs, {per_run}/run)"
        lines.append("  " * depth + f"- {nm} x{qty:,} [{label}]{note}")
        for mat_id, mat_qty in inputs(db, bp, act):
            expand(mat_id, mat_qty * runs, depth + 1)

    expand(type_id, quantity, 0)
    return lines


def aggregated_phases(db, type_id, quantity):
    """M5's shared-quantity aggregation, level by level.

    Same-type requirements merge per phase, then round runs once — not per
    parent. Returns a list of phases, target first; each phase is a list of
    (name, quantity, runs, activity) with runs=None marking terminators.
    """
    reqs = {type_id: quantity}
    phases = []
    while reqs:
        buildable = {}
        rows = []
        for t, qty in reqs.items():
            prod = producers(db, t)
            if prod:
                buildable[t] = (qty, prod[0])
            else:
                rows.append((type_name(db, t), qty, None, None))
        for t, (qty, (_, act, per_run)) in sorted(buildable.items()):
            label = ACTIVITY_LABELS.get(act, f"activity {act}")
            rows.append((type_name(db, t), qty, runs_for(qty, per_run), label))
        phases.append(rows)
        nxt = {}
        for _t, (qty, (bp, act, per_run)) in buildable.items():
            runs = runs_for(qty, per_run)
            for mat_id, mat_qty in inputs(db, bp, act):
                nxt[mat_id] = nxt.get(mat_id, 0) + mat_qty * runs
        reqs = nxt
    return phases


def raw_totals(phases):
    """Terminator quantities summed across the whole chain."""
    totals = {}
    for rows in phases:
        for nm, qty, runs, _ in rows:
            if runs is None:
                totals[nm] = totals.get(nm, 0) + qty
    return totals


def main():
    type_id = int(sys.argv[1]) if len(sys.argv) > 1 else 644
    quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    db = connect()

    print(f"=== per-branch tree: {type_name(db, type_id)} x{quantity:,} ===")
    print("\n".join(per_branch_tree(db, type_id, quantity)))

    phases = aggregated_phases(db, type_id, quantity)
    print()
    print("=== aggregated phases (shared intermediates merged) ===")
    for i, rows in enumerate(phases):
        print(f"phase {i}:")
        for nm, qty, runs, act in rows:
            if runs is None:
                print(f"  {nm:32s} {qty:>10,}  [raw]")
            else:
                print(f"  {nm:32s} {qty:>10,}  {act}, {runs:,} runs")

    print()
    print("=== raw-material acquisition table ===")
    totals = raw_totals(phases)
    known = {m for members in RAW_CATEGORIES.values() for m in members}
    for cat, members in RAW_CATEGORIES.items():
        rows = [(m, totals[m]) for m in members if m in totals]
        if rows:
            print(f"-- {cat}")
            for m, q in sorted(rows, key=lambda r: -r[1]):
                print(f"   {m:25s} {q:>10,}")
    stray = {m: q for m, q in totals.items() if m not in known}
    if stray:
        print("-- unclassified (extend RAW_CATEGORIES):", stray)


if __name__ == "__main__":
    main()
