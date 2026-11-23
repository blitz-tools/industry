# Structures

The facility registry under **Build Planner → Structures**: where industry
happens, and what multiplies. Every planner calculation is per-facility —
material and time bonuses from rigs and hulls, tax on install cost — so
the registry is the user-state side of that math (the SDE and market syncs
supply the rest).

## Registrations, not structures

A structure registers **per activity** (manufacturing, copying, invention,
reactions): an engineering complex can host manufacturing and copying at
once, so it appears in more than one group. Structure-level facts — name,
type, system, the supercapital-assembly capability — live on the structure;
the per-activity dials — rigs, tax, the default flag — live on the
registration.

Exactly **one default per activity** is enforced (setting a new default
demotes the previous one; unchecking leaves the activity default-less).
The planner pre-selects the default and the build plan can override per
job.

## Systems and security

Pick a solar system from the type-ahead (the systems your syncs have
resolved — ESI's search endpoint is gone, so anything else lands when a
sync observes it). The security class derives from it at save time via
ESI and is stored on the structure; the hand-set control only exists for
registrations without a system, where rig effectiveness still needs a
class.

The **supercapital assembly** flag is validated, not trusted:
engineering complexes in nullsec systems only. Community documentation
additionally points at sovereignty plus the *Supercapital Construction
Facilities* infrastructure-hub upgrade — an unconfirmed pin; the flag
gates the final hull job only, never the component builds.

## Import from sync

Player structures the asset sync has observed (blueprint, material, and
job locations) that aren't registered yet appear as import suggestions —
importing pre-fills the name and system; activity, type, rigs, and tax
still need a decision. Market hubs (structures with no industry lines)
are not distinguishable in the data and stay importable, but belong to
the market manager, not this registry. Restricted sightings (no rostered
character can dock) stay listed until a sync resolves them.

## What the planner multiplies

The reference card on the page shows the lookup layer the planner reads —
hull bonuses, rig tiers scaled by system security, tax plus the system
cost index. Values are pinned from live ESI dogma and fuzzwork's
industry calculator; provenance lives in `app/facilities.py`, and a CCP
balance pass is a data edit there, not a code change.
