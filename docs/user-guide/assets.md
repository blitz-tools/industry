# Assets

The **Assets** page (Character nav group) browses everything your
registered characters own, served entirely from synced data — page
renders never touch ESI.

## Syncing

Assets sync in the background on a schedule (roughly every 30 minutes)
and on demand via the **Sync now** button in the toolbar. The toolbar's
character picker shows per-character sync state: ok, stale, never
synced, or error, so you can see whose data is fresh before trusting a
count.

## Browsing

Assets are grouped **region → system → structure**, with per-structure
pagination and per-type row aggregation — a hangar with 4,000 units of
one module is one row. Each structure row opens a structure browser
listing its contents, sorted by quantity by default, with sortable
columns.

## Filters

- **Character / corporation picker** — collapsible corporation rows
  expanding to character cards; select all, none, or individual
  characters. The selection persists across visits.
- **Region** — the standard set of New Eden regions, limited to regions
  with assets under the current character filter.
- **Category** — materials, reactions, blueprints, ships, modules,
  drones, skills, implants, structures, and other. Options are dynamic:
  only buckets with assets under the current filters appear, and a
  selected-but-empty bucket stays visible.

Filter changes swap the page content in place without a full reload.

## Restricted structures

Structures your characters can't dock in (no access, or the structure is
abandoned) show as `Structure #<id>`. They are parked rather than
hammered — the resolver retries them only after a multi-day cooldown.
Names appear automatically once any character gains docking access and
the next sync runs.
