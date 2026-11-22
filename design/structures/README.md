# Structures mockup — the M3 surface

The first of the three surface mockups (M3 structure manager, M15 sync
panel, M12 capability surface — see [`../README.md`](../README.md)):
a single new page type proposed once against the reference component
set, unlike the chain sets' three-page convention. It is the
facility-registry CRUD surface the TODO spec describes, feeding M4's
facility defaults — every planner calculation multiplies against these
registrations (materials via ME rigs × security, time via hull bonus and
TE rigs, cost via tax and the M15 cost index).

| File | Shows |
|---|---|
| `structures.html` | The registry table grouped by activity (per structure × activity registrations, default badges, the supercapital-assembly capability flag), the add/edit form in edit state with the solar-system type-ahead open, the import-from-sync card (structures the asset sync has seen but that aren't registered — including the market-hub routing note), and the multiplier reference card the planner reads |

## New components proposed

- `.form-grid` with `.field` / `.field-label` / `.field-hint` /
  `.form-input` / `.form-select` / `.form-check` — the CRUD form layout
  (added to `../shared/mockups.css`; first form surface in the program)
- `.badge.hisec` / `.lowsec` / `.nullsec` — system-security markers
- `.badge.capability` — structure capability (supercapital assembly)
- Everything else reuses the reference set: `.autocomplete` (the
  planner's search dropdown, repurposed for system type-ahead),
  `.activity-tag` for the registry's activity groups, `.chip-button`
  for activity selection, `.icon-button` for row edit/delete,
  `.sync-source` for provenance lines

## Design positions taken (flagged in `.anno` boxes on the page)

- **Registrations are per structure × activity** — an engineering
  complex covers manufacturing, invention, and copying simultaneously,
  so one structure can hold registrations in several groups; rigs and
  the default flag live on the registration.
- **Security derives from the selected system** (ESI
  `security_status`), refining the TODO spec's hand-entered field; the
  manual control only exists for registrations without a system.
- **Default demotion**: setting a new default in an activity group
  demotes the previous one (proposed over leaving activities
  default-less).
- **Import-from-sync card**: a proposal beyond the TODO spec — the 11
  player structures `universe_locations` has observed become import
  suggestions that pre-fill the form, rather than a second manual
  entry path. NPC stations don't appear there (complete SDE/ESI data —
  search-and-select in the form instead).
- **The two facility-class pins stay visible**: supercapital assembly
  (Hel/Ragnarok — capability flag on the form, security-validated:
  confirmed 2026-11-22 that no Amamake lowsec facility can hold it,
  with the nullsec-player-structure requirement a pin needing CCP-docs
  confirmation; no registered structure holds it today, so supercap
  chains surface it as an acquisition gap on the final hull job) and
  biochemical reactions (Crash — open question annotated on the
  reactions group, not answered by the mockup).
- **Market hubs don't register here** (corrected 2026-11-22): the
  corp's "5 times nearly AT winners" is a Keepstar market hub — no
  industry lines. It appears in the import card as an unimportable
  routing note and belongs to the market manager (the M15 sync-panel
  surface): industry facilities in this registry, markets there.
- **Copying absent from the activity enum** — flagged for the M3/M9
  boundary: copy jobs need a facility default too.

## Data provenance

- Structure names and systems are real, from the live
  `universe_locations` table (asset sync 2026-11-16): the five
  registered player structures, the four import candidates, the two
  restricted `Structure #…` rows, and the Osoggur NPC station are all
  synced rows. Amamake's 0.3 / Osoggur's 0.4 / Hek's 0.7 security
  statuses are well-known public values.
- **Structure types, rigs, tax rates, and capability flags are
  invented for the demo** — `universe_locations` does not know them;
  they are exactly the user-entered fields this page exists to
  capture. One real-world correction is baked in (2026-11-22):
  "Amamake - 5 times nearly AT winners" is a Keepstar market hub, so
  it never registers as an industry facility; "Amamake - Police
  Weapons Facility" is the manufacturing and copying site and
  "Amamake - Reactions & Reprocessing" the refinement-and-reactions
  site (product-owner confirmed).
- Multiplier values in the reference card: the engineering-complex
  hull bonuses (15/30/50%) are CCP-documented; the rig and reaction
  values are illustrative until confirmed from CCP structure docs at
  implementation (the M3 scope note's instruction).
- System cost indices are **not present** — they sync in M15's
  world-state band; the form and multiplier card carry that dependency.

## Milestone mapping

| Mockup section | Milestone |
|---|---|
| Registry table, add/edit form, defaults | M3 structure manager |
| Solar-system type-ahead, security derivation | M3 (ESI universe lookup) |
| Import-from-sync card | M3 (on top of the landed asset sync) |
| Multiplier reference card | M3 lookup table → M4 facility math |
| Cost-index dependency notes | M15 world-state band |
| Supercapital-assembly capability | M3 pin (surfaced by HEL-CHAIN / RAGNAROK-CHAIN) |
| Biochemical facility-class question | M3 pin (surfaced by CRASH-CHAIN) |
| Copying / activity-enum question | M3 ↔ M9 boundary |
