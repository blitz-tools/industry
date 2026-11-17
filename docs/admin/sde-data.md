# SDE data

Blueprint recipes — materials, products, required skills, activity
durations — live in the EVE **Static Data Export** (SDE), not ESI. ESI
cannot answer "what does this blueprint build from"; it supplies what the
SDE can't: which blueprints you own, who you are (skills), what's
installed (jobs), and where things sit (assets). The application mirrors
the SDE locally so recipe queries are plain database joins.

## The verbatim mirror

The `sde_*` tables are a **verbatim mirror** of the fuzzwork SQLite dump
(latest stable release, ~141 MiB gzipped): same columns, same rows,
duplicates included. There is no application-side migration and no ORM
involved — the import drops and recreates each table in one transaction,
so a dump schema change can never break it.

Interpreting the data (blueprint → product joins, skill dedup, activity
labels) belongs to the consuming query layer, never the import.

The initial import on a fresh deployment is the administrator's call:

```sh
podman compose -f compose.dev.yml run --rm dev python -m app.sde import
podman compose -f compose.dev.yml run --rm dev python -m app.sde info
```

(Any Docker-compatible compose runtime works too, as does plain `uv run`
outside a container.)

## Automatic maintenance

A background loop polls hourly but performs a real check at most once
every 24 hours (a persisted gate, so restarts don't reset it). The check
compares the published dump MD5 sidecar; on a changed hash the mirror is
dropped and re-imported wholesale — there is no diffing. The loop only
**maintains an existing mirror**: it never performs the initial import on
a fresh deployment.

## Admin page

**Admin → SDE Data** in the application shows the last check, last
import, current release, outcome, and table counts, plus the controls:

- **Import now** — forced full re-import, behind a confirm dialog.
- **Check now** — the cheap MD5-only check, without downloading.
- **Pause automatic imports** — persisted across re-imports.
- **Stop current import** — cooperative cancel between download chunks;
  the previous mirror stays intact.
