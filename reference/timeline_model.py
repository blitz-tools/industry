#!/usr/bin/env python3
"""Time-balanced work-distribution and timeline model (proof-out v2).

Executable spec for M9's job orchestration and M12's blueprint asset gap
analysis; regenerates TYPHOON-CHAIN.md's v2 model, timelines, scaling and
horizon tables, and BPO recommendations. Run inside the dev container:

    podman exec industry_dev_1 python reference/timeline_model.py 644 100
    podman exec industry_dev_1 python reference/timeline_model.py 644 100 \
        --timelines 10,25,50,100
    podman exec industry_dev_1 python reference/timeline_model.py 644 100 --bpo

Everything here is computed, never assumed globally:

- Skill multipliers are PER CHARACTER, read from the synced `skills` table
  (see MFG_SKILL_MAPPING for the unverified dogma mapping this plumbing
  awaits). The proof-outs used the max-skills scenario (0.68) — a scenario,
  not a constant: the live roster already diverges (theblitzrage holds
  Advanced Industry 1 -> 0.776 where Octavia holds 5 -> 0.68), so a real
  model must weight per assignment, which is M9's efficiency input.
- Times are per blueprint, from `industryActivity` (manufacturing 1,
  copying 5, reactions 11).
- Slot pools, reaction concurrency (1 BPO per formula per character), and
  copy concurrency (1 job per BPO) come from the roster and the blueprint
  job-lock — never from slots alone.

Strategies for the horizon table: "copy" (pure copy), "hybrid" (copy the
longest queue until inputs arrive, then build direct — applies when skilled
build time beats copy time per run), "2bpo" (a second BPO for the longest
queue). See TYPHOON-CHAIN.md's copy-vs-direct decision rule.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chain_expand import connect, inputs, producers, runs_for, type_name

WINDOW = 6.0  # login-window hours (plan parameter)
SLOTS_PER_CHAR = 10  # max skills; separate pools per activity
DEFAULT_CORP = 98830898
BASE_N = 100  # quantity for rate derivation and the default report

# UNVERIFIED dogma mapping (M4's data-table task): skill id -> manufacturing
# time reduction per level, multiplicative. Whether copying/reactions are
# skill-reducible is also unverified; the model leaves them unadjusted.
MFG_SKILL_MAPPING = {3380: 0.04, 3388: 0.03}  # Industry, Advanced Industry
MAX_SKILL_MULT = 0.68  # Industry 5 x Advanced Industry 5 (doc scenario)


def bp_time(db, bp_type_id, activity):
    """Hours per run for one blueprint activity."""
    row = db.execute(
        "SELECT time FROM sde_industryActivity WHERE typeID=? AND activityID=?",
        (bp_type_id, activity),
    ).fetchone()
    return (row[0] if row else 0) / 3600.0


def max_runs(db, bp_type_id):
    """maxProductionLimit — the job/BPC run-count ceiling."""
    row = db.execute(
        "SELECT maxProductionLimit FROM sde_industryBlueprints WHERE typeID=?",
        (bp_type_id,),
    ).fetchone()
    return row[0] if row else 10**9


def char_rows(db, corp_id):
    return list(
        db.execute(
            "SELECT character_id, name FROM characters"
            " WHERE corporation_id=? ORDER BY name",
            (corp_id,),
        )
    )


def skill_mult(db, character_id):
    """Manufacturing time multiplier for one character, from synced skills."""
    mult = 1.0
    for skill_id, per_level in MFG_SKILL_MAPPING.items():
        row = db.execute(
            "SELECT active_skill_level FROM skills"
            " WHERE owner_type='character' AND owner_id=? AND skill_id=?",
            (character_id, skill_id),
        ).fetchone()
        mult *= 1.0 - per_level * (row[0] if row else 0)
    return mult


def even_split(total, jobs):
    """[(run_count, n_jobs)] — synchronized end times within one run."""
    base, extra = divmod(total, jobs)
    sizes = []
    if extra:
        sizes.append((base + 1, extra))
    if jobs - extra:
        sizes.append((base, jobs - extra))
    return sizes


def expand(db, type_id, quantity):
    """Level-by-level aggregation; [{type_id: (qty, bp, activity, per_run)}]."""
    reqs = {type_id: quantity}
    phases = []
    while reqs:
        buildable = {}
        for t, qty in reqs.items():
            prod = producers(db, t)
            if prod:
                bp, act, per_run = prod[0]
                buildable[t] = (qty, bp, act, per_run)
        if buildable:
            phases.append(buildable)
        nxt = {}
        for _t, (qty, bp, act, per_run) in buildable.items():
            runs = runs_for(qty, per_run)
            for mat_id, mat_qty in inputs(db, bp, act):
                nxt[mat_id] = nxt.get(mat_id, 0) + mat_qty * runs
        reqs = nxt
    return phases


def model(db, type_id, quantity, n_chars, mfg_mult):
    """Per-phase job plan. mfg_mult is per-character in reality; a scalar
    models the shared-levels scenario (M9 computes it per assignment)."""
    pool = n_chars * SLOTS_PER_CHAR
    rxn_concurrency = n_chars  # 1 reaction BPO per formula per character
    out = []
    for pnum, buildable in enumerate(expand(db, type_id, quantity)):
        items = []
        for t, (qty, bp, act, per_run) in sorted(buildable.items()):
            runs = runs_for(qty, per_run)
            is_rxn = act == 11
            t_copy = bp_time(db, bp, 5)
            if is_rxn:
                t_run = bp_time(db, bp, 11)
                jobs = min(rxn_concurrency, runs)  # blueprint job-lock
            else:
                t_run = bp_time(db, bp, 1) * mfg_mult
                k = min(max_runs(db, bp), max(1, math.ceil(runs / pool)))
                jobs = math.ceil(runs / k)
            items.append(
                dict(
                    type_id=t, name=type_name(db, t), qty=qty, runs=runs,
                    is_rxn=is_rxn, jobs=jobs, sizes=even_split(runs, jobs),
                    t_run=t_run, t_copy=t_copy,
                    dur=max(b for b, _ in even_split(runs, jobs)) * t_run,
                    copy_h=None if is_rxn else runs * t_copy,
                )
            )
        out.append(
            dict(num=pnum, items=items,
                 is_rxn=bool(items) and all(i["is_rxn"] for i in items))
        )
    return dict(phases=out, pool=pool, n_chars=n_chars)


def schedule(m, strategy="copy"):
    """Serial-phase timeline in days.

    Each phase starts when its inputs exist AND its BPCs are copied.
    Strategies reshape only the longest copy queue per manufacturing phase.
    Returns (rows, end, phase_ends): rows are (label, start, end) in days;
    phase_ends maps phase number -> (start, end).
    """
    pool = m["pool"]
    rows = []
    phase_ends = {}
    prev_end = 0.0
    for phase in reversed(m["phases"]):  # deepest first
        if phase["is_rxn"]:
            dur = max(i["dur"] for i in phase["items"]) / 24
            rows.append((f'phase {phase["num"]} rxn', prev_end, prev_end + dur))
            phase_ends[phase["num"]] = (prev_end, prev_end + dur)
            prev_end += dur
            continue
        copies = [i for i in phase["items"] if i["copy_h"]]
        if strategy == "2bpo" and copies:
            max(copies, key=lambda i: i["copy_h"])["copy_h"] /= 2
        copy_ends = [i["copy_h"] / 24 for i in copies]
        start = max([prev_end] + copy_ends)
        slot_hours = sum(i["runs"] * i["t_run"] for i in phase["items"])
        max_dur = max(i["dur"] for i in phase["items"]) / 24
        dur = max(max_dur, slot_hours / pool / 24)
        if strategy == "hybrid" and copies:
            # Copy the longest queue until inputs arrive, then build direct
            # (applies when t_run < t_copy per run — the decision rule).
            longest = max(copies, key=lambda i: i["copy_h"])
            overflow_d = longest["copy_h"] / 24 - prev_end
            if overflow_d > 0 and longest["t_run"] < longest["t_copy"]:
                direct_d = overflow_d * longest["t_run"] / longest["t_copy"]
                start = prev_end
                dur = max(dur, direct_d)
        if start > prev_end + 1e-9:
            rows.append((f'dead zone before phase {phase["num"]}',
                         prev_end, start))
        rows.append((f'phase {phase["num"]} mfg', start, start + dur))
        phase_ends[phase["num"]] = (start, start + dur)
        for i in copies:
            rows.append((f'copy {i["name"]}', 0.0, i["copy_h"] / 24))
        prev_end = start + dur
    return rows, prev_end, phase_ends


def print_report(db, type_id, quantity, corp_id, mfg_mult):
    chars = char_rows(db, corp_id)
    m = model(db, type_id, quantity, len(chars), mfg_mult)
    print(f"=== {type_name(db, type_id)} x{quantity:,} — time-balanced model ===")
    print(f"pool: {len(chars)} characters x {SLOTS_PER_CHAR} slots;"
          f" scenario multiplier {mfg_mult:.3f}")
    print("per-character manufacturing multipliers (computed from skills):")
    for cid, nm in chars:
        print(f"  {nm:20s} {skill_mult(db, cid):.3f}")
    for phase in m["phases"]:
        kind = "REACTION" if phase["is_rxn"] else "MANUFACTURING"
        print(f'-- phase {phase["num"]} ({kind})')
        for i in phase["items"]:
            bpc = ", ".join(f"{c}x{b}" for b, c in i["sizes"])
            what = "BPO jobs" if i["is_rxn"] else "BPCs"
            windows = math.ceil(i["dur"] / WINDOW)
            print(
                f'  {i["name"]:30s} {i["qty"]:>8,} u -> {i["runs"]:>5,} runs'
                f"  {i['jobs']} {what}: {bpc}  ({i['dur']:.1f}h ="
                f" {windows} window{'s' if windows > 1 else ''})"
            )
    copies = [
        (p["num"], i) for p in m["phases"] for i in p["items"] if i["copy_h"]
    ]
    print()
    print("=== copy pipeline (parallel across types, sequential per BPO) ===")
    for _, i in sorted(copies, key=lambda c: -c[1]["copy_h"]):
        desc = ", ".join(f"{c}x{b}" for b, c in i["sizes"])
        print(f'  {i["name"]:30s} {i["jobs"]:>3} BPCs ({desc})'
              f'  copy {i["copy_h"]:>7,.0f}h = {i["copy_h"] / 24:>5.1f}d')
    rows, end, _ = schedule(m)
    print()
    print("=== serial timeline (days) ===")
    for label, a, b in rows:
        print(f"  {label:38s} {a:7.1f} -> {b:7.1f}")
    print(f"  chain end: {end:.1f} days")


def print_timelines(db, type_id, corp_id, mfg_mult, counts):
    chars = char_rows(db, corp_id)
    width = 56
    for n in counts:
        m = model(db, type_id, n, len(chars), mfg_mult)
        rows, end, _ = schedule(m)
        print(f"=== {type_name(db, type_id)} x{n} — end {end:.1f}d"
              f" ({end / n:.2f} d/unit, pool {m['pool']} slots) ===")
        for label, a, b in rows:
            i0 = int(a / end * width)
            i1 = max(i0 + 1, int(b / end * width))
            ch = "." if "dead" in label else ("#" if "copy" in label else "m")
            print(f"  {label:38s} |{ch * (i1 - i0):<{width}}|"
                  f" {a:6.1f} -> {b:6.1f}d")
        print()


def print_horizon(db, type_id, corp_id, mfg_mult, horizons=(7, 14, 30, 60, 90)):
    """Largest target count whose chain ends within each horizon."""
    chars = char_rows(db, corp_id)
    print("=== target count per completion horizon ===")
    print(f"{'horizon':>9} {'pure copy':>10} {'hybrid':>8} {'2x BPO':>8}")
    strategies = ("copy", "hybrid", "2bpo")

    def end_for(n, strategy):
        m = model(db, type_id, n, len(chars), mfg_mult)
        return schedule(m, strategy)[1]

    for days in horizons:
        row = []
        for strategy in strategies:
            best = 0
            for n in range(1, 400):
                if end_for(n, strategy) <= days:
                    best = n
                else:
                    break
            row.append(best)
        print(f"{days:>8}d {row[0]:>10} {row[1]:>8} {row[2]:>8}")


def print_bpo(db, type_id, quantity, corp_id, mfg_mult):
    """M12's blueprint asset gap analysis: per-commodity BPO recommendations.

    A commodity's input-ready line T_in(N) is the scheduled end of the next
    deeper phase (the phase producing its inputs), fitted linearly from two
    quantities. Rates are per target unit and scale-invariant; the trigger
    count solves queue(N) = T_in(N) — the largest N where one BPO suffices.
    """
    chars = char_rows(db, corp_id)
    n_chars = len(chars)
    m = model(db, type_id, quantity, n_chars, mfg_mult)
    pool = m["pool"]

    def phase_ends(n):
        return schedule(model(db, type_id, n, n_chars, mfg_mult))[2]

    ends_n, ends_2n = phase_ends(quantity), phase_ends(quantity * 2)

    print(f"=== BPO obtainment recommendations ({type_name(db, type_id)}"
          f" x{quantity:,}) ===")
    print(f"pool {pool} slots, {n_chars} reaction BPOs per formula;"
          " input-ready rates fitted under the pure-copy strategy")
    print(f"{'commodity':30s} {'queue d/unit':>12} {'T_in d/unit':>11}"
          f" {'min BPOs':>9} {'1-BPO max N':>12} {'slot ceiling':>12}")
    for phase in m["phases"]:
        deeper = phase["num"] + 1
        if deeper in ends_n:
            t_in_rate = (ends_2n[deeper][1] - ends_n[deeper][1]) / quantity
            t_in_fixed = ends_n[deeper][1] - t_in_rate * quantity
        else:
            t_in_rate, t_in_fixed = 0.0, 0.0  # deepest phase: chain start
        for i in phase["items"]:
            if not i["copy_h"]:
                continue
            queue_rate = i["copy_h"] / 24 / quantity
            if t_in_rate < 1e-9 and t_in_fixed < 1e-9:
                min_txt = "lead only"
                trig_txt = "n/a"
            else:
                min_bpos = max(1, math.ceil(queue_rate / t_in_rate))
                min_txt = str(min_bpos)
                if queue_rate > t_in_rate:
                    trigger = t_in_fixed / (queue_rate - t_in_rate)
                    trig_txt = f"~{trigger:,.0f}"
                else:
                    trig_txt = "all N"
            ceiling = math.ceil(pool * i["t_copy"] / i["t_run"])
            print(f'{i["name"]:30s} {queue_rate:>12.4f} {t_in_rate:>11.4f}'
                  f" {min_txt:>9} {trig_txt:>12} {ceiling:>12}")
    print("(min BPOs = ceil(queue rate / input-ready rate) — the count that"
          " fits the copy queue into the input dead zone; slot ceiling ="
          " BPOs past which BPCs arrive faster than slots build;"
          " 'lead only' = deepest phase, no input gating)")


def main():
    args = sys.argv[1:]
    type_id = int(args[0]) if args else 644
    quantity = int(args[1]) if len(args) > 1 else BASE_N
    corp_id = DEFAULT_CORP
    mfg_mult = MAX_SKILL_MULT
    timelines = None
    do_bpo = do_horizon = False
    rest = args[2:]
    while rest:
        arg = rest.pop(0)
        if arg == "--timelines":
            timelines = [int(x) for x in rest.pop(0).split(",")]
        elif arg == "--bpo":
            do_bpo = True
        elif arg == "--horizon":
            do_horizon = True
        elif arg == "--corp":
            corp_id = int(rest.pop(0))
        elif arg == "--char":
            char_id = int(rest.pop(0))
            db = connect()
            mfg_mult = skill_mult(db, char_id)
    db = connect()
    if timelines:
        print_timelines(db, type_id, corp_id, mfg_mult, timelines)
    if do_bpo:
        print_bpo(db, type_id, quantity, corp_id, mfg_mult)
    if do_horizon:
        print_horizon(db, type_id, corp_id, mfg_mult)
    if not (timelines or do_bpo or do_horizon):
        print_report(db, type_id, quantity, corp_id, mfg_mult)


if __name__ == "__main__":
    main()
