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
  below are hardcoded to the chains resolved so far (Typhoon, Charon,
  Panther, Jackdaw, Trimark II, Scourge Rage HAM); M5 should classify
  through invGroups/invCategories instead — the SDE groups map cleanly
  for everything except molecular-forging tools ('Commodities'
  catch-all) and Morphite (filed under 'Mineral' despite being the top
  moon material) — both need the name-list fallback. T3 adds two
  terminator classes the material walk never sees (they enter only
  through the invention overlay): the invention relics themselves
  ('Ancient Relics' category, e.g. Sleeper Hull Relics) and the Sleeper
  salvage ('Ancient Salvage' group, 19 types — maps cleanly) that feeds
  the hybrid tech components. T2 rig chains add the wreck salvage
  ('Salvaged Materials' group, 41 types — maps cleanly) that rig
  manufacturing consumes (T1 rigs eat the damaged variants — Fried/
  Contaminated/Smashed; T2 the intact ones).
- Invention (activity 8) is an overlay, not part of the material walk:
  the invented blueprint's build inputs resolve normally, and the
  invention recipe (source BPC, probability, datacores, skills) is
  reported by the invention-layer section at the end. The source-BPC
  run consumed per attempt is implicit in the game (1 run/attempt) and
  absent from the SDE material list. Three flavors, dispatched on the
  probability rows for the product blueprint: T2 has one source BPC
  (decryptor scenarios apply) — its activity-8 recipe may carry
  alternative products alongside the target (T2 ammo: Rage or Javelin
  BPC, each with its own probability row — sibling rolls, not the T3
  grade mechanism); T3 reverse engineering has one row per relic
  grade — the relic item itself carries activity 8, the grade sets
  both probability and BPC runs (the activity-8 product quantity),
  and the T2 decryptor/base-ME conventions do not apply (pin at M8).
  BPC runs per success is the activity-8 product quantity in the SDE
  (1 for ships and rigs, 10 for T2 ammo) — the live blueprints table
  can disagree (owned rig BPCs read 2 runs), so owned BPCs always
  report their ESI-synced values and only projections use the SDE
  quantity (pin at M8).
- Cycle detection is NOT implemented here (the manufacturing chain has none);
  M5's resolver must add it defensively per the milestone scope.
"""

import math
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "industry.db"

ACTIVITY_LABELS = {1: "manufacturing", 5: "copying", 8: "invention", 11: "reaction"}

# Decryptor modifiers for invention, pinned from live ESI dogma 2026-11-19
# (universe/types/{id} dogma_attributes; names via /dogma/attributes/):
# inventionPropabilityMultiplier 1112, inventionMEModifier 1113,
# inventionTEModifier 1114, inventionMaxRunModifier 1124. Rows:
# (name, probability multiplier, ME modifier, TE modifier, max-run modifier).
# NOT in the SDE mirror (dogma tables are not imported) — re-pin if CCP
# rebalances. Invented-BPC base ME/TE is likewise absent from SDE/ESI
# (community-documented -4/-4, BASE_INVENTED_ME below) — pin at M8.
BASE_INVENTED_ME = -4
DECRYPTORS = [
    ("Accelerant", 1.2, 2, 10, 1),
    ("Attainment", 1.8, -1, 4, 4),
    ("Augmentation", 0.6, -2, 2, 9),
    ("Parity", 1.5, 1, -2, 3),
    ("Process", 1.1, 3, 6, 0),
    ("Symmetry", 1.0, 1, 8, 2),
    ("Optimized Attainment", 1.9, 1, -2, 2),
    ("Optimized Augmentation", 0.9, 2, 0, 7),
]

# Hardcoded to the chains resolved so far — see module docstring.
RAW_CATEGORIES = {
    "minerals": [
        "Tritanium", "Pyerite", "Mexallon", "Isogen",
        "Nocxium", "Zydrine", "Megacyte",
    ],
    "moon materials": [
        # R4 (Typhoon chain)
        "Hydrocarbons", "Silicates", "Atmospheric Gases", "Evaporite Deposits",
        # R8-R64 (Charon chain's advanced reactions)
        "Cadmium", "Caesium", "Mercury", "Titanium", "Chromium", "Hafnium",
        "Dysprosium", "Neodymium", "Promethium", "Thulium",
        # Panther chain's T2-component reactions
        "Vanadium", "Scandium", "Platinum", "Technetium",
        # Top moon material — invGroups files it under 'Mineral'; the
        # name-list fallback keeps it here.
        "Morphite",
    ],
    "PI commodities": [
        # Tier 1-3 (Typhoon chain)
        "Chiral Structures", "Water", "Test Cultures", "Viral Agent",
        "Supertensile Plastics", "Nanites", "Robotics", "Enriched Uranium",
        "Mechanical Parts", "Coolant",
        # Tier 4 (Charon chain's capital components)
        "Wetware Mainframe", "Broadcast Node", "Self-Harmonizing Power Core",
        "Organic Mortar Applicators", "Integrity Response Drones",
    ],
    "ice products": [
        "Strontium Clathrates", "Oxygen", "Heavy Water", "Liquid Ozone",
        "Helium Isotopes", "Nitrogen Isotopes", "Oxygen Isotopes",
        "Hydrogen Isotopes",
    ],
    # SDE group 'Harvestable Cloud': wormhole fullerites (T2-style advanced
    # reactions) and k-space mykoserocins/cytoserocins (gas sites).
    "gas (harvestable clouds)": [
        "Fullerite-C28", "Fullerite-C32", "Fullerite-C50", "Fullerite-C60",
        "Fullerite-C70", "Fullerite-C72", "Fullerite-C84", "Fullerite-C320",
        "Fullerite-C540", "Amber Mykoserocin", "Golden Mykoserocin",
        "Amber Cytoserocin", "Golden Cytoserocin", "Lime Cytoserocin",
    ],
    # Market-acquired NPC goods: molecular-forging tools used in gas
    # reactions, construction blocks consumed by T2 components. Group
    # 'Commodities' is a catch-all, so no SDE group maps here — M5
    # needs a name-list fallback for these.
    "npc market goods": [
        "AG-Composite Molecular Condenser",
        "Construction Blocks",
        # T2-ammo fuel additive: no producing blueprint anywhere in the
        # SDE — NPC-seeded per community docs, verify against M15
        # market data.
        "Rocket Fuel",
        # Booster-chain consumables (Crash chain): Spirits ('General'
        # group) and Hydrochloric Acid ('Biohazard' group) — no
        # producers, NPC trade goods.
        "Spirits",
        "Hydrochloric Acid",
    ],
    # Sleeper salvage (w-space site drops) consumed by hybrid tech
    # components. The SDE group 'Ancient Salvage' maps cleanly (19
    # types); the 15 below are the Jackdaw chain's members.
    "sleeper salvage": [
        "Modified Fluid Router", "Cartesian Temporal Coordinator",
        "Electromechanical Hull Sheeting", "Powdered C-540 Graphite",
        "Neurovisual Input Matrix", "Melted Nanoribbons",
        "Fused Nanomechanical Engines", "Resonance Calibration Matrix",
        "Central System Controller", "Defensive Control Node",
        "Emergent Combat Intelligence", "Heuristic Selfassemblers",
        "Jump Drive Control Nexus", "Thermoelectric Catalysts",
        "Emergent Combat Analyzer",
    ],
    # Wreck salvage (k-space, salvager module) consumed by rig
    # manufacturing. The SDE group 'Salvaged Materials' maps cleanly
    # (41 types); the 3 below are the Trimark II chain's members —
    # T2 rigs eat the intact variants, T1 the damaged ones (Fried/
    # Contaminated/Smashed), which this chain never walks.
    "wreck salvage": [
        "Interface Circuit", "Intact Armor Plates", "Nanite Compound",
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
    Printed phase numbers count up in build order instead (decided
    2026-11-18, matching the waves): the all-raw final level is phase 0,
    the deepest buildable level is phase 1, the target is the highest.
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


def invention_sources(db, product_bp_id):
    """All invention recipes producing a blueprint:
    [(source_type_id, probability, runs_per_success)].

    T2 has a single row (the source BPC, runs 1). T3 relic reverse
    engineering has one row per relic grade; the grade sets both the
    probability and the BPC runs per success, the latter read from the
    activity-8 product quantity (20/10/3 for small hull sections).
    """
    rows_ = db.execute(
        "SELECT typeID, probability FROM sde_industryActivityProbabilities"
        " WHERE productTypeID=?",
        (product_bp_id,),
    ).fetchall()
    out = []
    for source, probability in rows_:
        runs = db.execute(
            "SELECT quantity FROM sde_industryActivityProducts"
            " WHERE typeID=? AND activityID=8 AND productTypeID=?",
            (source, product_bp_id),
        ).fetchone()
        out.append((source, probability, runs[0] if runs else 1))
    return out


def invention_source(db, product_bp_id):
    """The T2 invention recipe producing a blueprint, if any.

    Returns (source_bp_id, probability, [(material_name, qty)],
    [(skill_name, level)]) or None. The source BPC run consumed per
    attempt is implicit in the game and absent from the SDE materials.
    """
    srcs = invention_sources(db, product_bp_id)
    if not srcs:
        return None
    # One product blueprint per T2 invention recipe in practice; take
    # the first like producers() does.
    source_bp, probability, _runs = srcs[0]
    mats = [
        (type_name(db, m), q) for m, q in inputs(db, source_bp, 8)
    ]
    skills = db.execute(
        "SELECT s.skillID, s.level FROM sde_industryActivitySkills s"
        " WHERE s.typeID=? AND s.activityID=8",
        (source_bp,),
    ).fetchall()
    return (
        source_bp,
        probability,
        mats,
        [(type_name(db, sk), lvl) for sk, lvl in skills],
    )


def invention_section(db, product_bp_id, bpcs_needed=1):
    """Lines for the invention overlay, dispatched on the probability
    rows: one source renders the T2 recipe (decryptor scenarios);
    multiple sources render the T3 relic-grade table."""
    srcs = invention_sources(db, product_bp_id)
    if not srcs:
        return []
    if len(srcs) > 1:
        return relic_invention_section(db, product_bp_id, srcs, bpcs_needed)
    src = invention_source(db, product_bp_id)
    if src is None:
        return []
    source_bp, p, mats, skills = src
    base_runs = srcs[0][2]
    siblings = [
        type_name(db, t)
        for (t,) in db.execute(
            "SELECT DISTINCT productTypeID FROM sde_industryActivityProducts"
            " WHERE typeID=? AND activityID=8 AND productTypeID != ?",
            (source_bp, product_bp_id),
        )
    ]
    out = [
        f"=== invention layer: {type_name(db, product_bp_id)} ===",
        f"source: {type_name(db, source_bp)} (blueprint {source_bp},"
        " activity 8, invention)",
        f"probability: {p:.2f} base (SDE); skill levels are assumed NOT to"
        " modify it post-Crius — pin at M8",
        "materials per attempt: "
        + ", ".join(f"{q} {m}" for m, q in mats),
        "skills: " + ", ".join(f"{s} {lvl}" for s, lvl in skills),
        "T1 consumption: 1 run of the source BPC per attempt (implicit,"
        " not in the SDE material list)",
        f"BPC runs per success: {base_runs:,} (SDE activity-8 product"
        " quantity). Owned BPCs report their ESI-synced runs instead —"
        " live rig BPCs read 2 against an SDE 1 (unexplained — pin"
        " at M8)",
    ]
    if siblings:
        out.append(
            "alternative products: "
            + ", ".join(siblings)
            + " — the same attempt recipe carries their probability rows"
            " too (sibling rolls, not the T3 grade mechanism); the"
            " planner must decide whether successes on siblings count"
            " as by-products or misses — pin at M8"
        )
    out += [
        "",
        f"need {bpcs_needed} successful invention(s);"
        f" expected attempts each = 1/p = {1 / p:.2f}",
        "expected datacores per success: "
        + ", ".join(f"{q / p:.0f} {m}" for m, q in mats),
        "confidence (no decryptor), P(>=1 success in n attempts): "
        + "  ".join(
            f"n={n}: {100 * (1 - (1 - p) ** n):.0f}%" for n in (4, 7, 10, 15)
        ),
        "",
        "decryptor scenarios (modifiers pinned from ESI dogma"
        " 2026-11-19; invented-BPC base ME/TE -4/-4 per community docs,"
        " pin at M8):",
        "  decryptor               p_eff  E[attempts]  ME_eff  TE  runs",
    ]
    for name, mult, me, te, runmod in DECRYPTORS:
        p_eff = p * mult
        out.append(
            f"  {name:24s} {p_eff:.2f}  {1 / p_eff:11.2f}"
            f"  {BASE_INVENTED_ME + me:+5d}  {te:+d}  {base_runs + runmod:,}"
        )
    out.append(
        f"\n  runs = invented-BPC run count ({base_runs:,} base +"
        " max-run modifier); more runs per BPC mean fewer inventions"
        " at scale"
    )
    return out


def relic_invention_section(db, product_bp_id, srcs, bpcs_needed=1):
    """Lines for the T3 reverse-engineering overlay: one row per relic
    grade. The relic item itself carries activity 8; the grade sets
    both probability and BPC runs per success. Decryptors and the T2
    base ME/TE (-4/-4) do not apply — pins at M8."""
    first_source = srcs[0][0]
    mats = [(type_name(db, m), q) for m, q in inputs(db, first_source, 8)]
    skills = [
        (type_name(db, sk), lvl)
        for sk, lvl in db.execute(
            "SELECT skillID, level FROM sde_industryActivitySkills"
            " WHERE typeID=? AND activityID=8",
            (first_source,),
        )
    ]
    prods = [
        type_name(db, p)
        for (p,) in db.execute(
            "SELECT DISTINCT productTypeID FROM sde_industryActivityProducts"
            " WHERE typeID=? AND activityID=8",
            (first_source,),
        )
    ]
    out = [
        f"=== invention layer (T3 relic reverse engineering):"
        f" {type_name(db, product_bp_id)} ===",
        "source: the relic item itself is the invention 'blueprint' —"
        " activity 8 lives on the relic's typeID, and 1 relic is consumed"
        " per attempt (implicit, like the T1 source-BPC run in T2;"
        " absent from the SDE material list)",
        "recipe shared across: " + ", ".join(prods)
        + " — the job targets one output; the probability row applies to"
        " the targeted blueprint",
        "materials per attempt: "
        + ", ".join(f"{q} {m}" for m, q in mats)
        + " (identical across grades)",
        "skills: " + ", ".join(f"{s} {lvl}" for s, lvl in skills),
        "",
        "grade table (SDE):",
        "  grade                              p   runs/success"
        "  E[attempts]  E[relics]  E[datacores per success]",
    ]
    for source, p, runs in srcs:
        out.append(
            f"  {type_name(db, source):34s} {p:.2f}  {runs:>12,}"
            f"  {1 / p:11.2f}  {1 / p:9.2f}"
            + "  " + " + ".join(f"{q / p:.1f}" for _m, q in mats)
        )
    out += [
        "",
        f"successes needed for {bpcs_needed} target(s) ="
        " ceil(target / runs-per-success) — a single success over-delivers"
        " at small targets (excess runs are inventory)",
        "T3 pins (community-documented, absent from SDE/ESI — pin at M8):"
        " invented-BPC ME/TE is fixed per grade (not the T2 -4/-4 base),"
        " decryptors do not apply to relic reverse engineering, and any"
        " skill effect on probability is unverified",
    ]
    return out


def main():
    type_id = int(sys.argv[1]) if len(sys.argv) > 1 else 644
    quantity = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    db = connect()

    print(f"=== per-branch tree: {type_name(db, type_id)} x{quantity:,} ===")
    print("\n".join(per_branch_tree(db, type_id, quantity)))

    phases = aggregated_phases(db, type_id, quantity)
    print()
    print("=== aggregated phases (shared intermediates merged) ===")
    depth = len(phases)
    for i, rows in enumerate(phases):
        print(f"phase {depth - 1 - i}:")
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

    # Invention overlay: the target's producing blueprint, when it is
    # invention-sourced (T2/T3), reports its acquisition recipe.
    prod = producers(db, type_id)
    if prod:
        inv = invention_section(db, prod[0][0])
        if inv:
            print()
            print("\n".join(inv))


if __name__ == "__main__":
    main()
