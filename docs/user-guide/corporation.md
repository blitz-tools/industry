# Corporation

The **Corporation** section targets exactly one corporation: the one the
[main character](characters.md) belongs to. All characters can be
registered, but the Corporation section follows the main.

## The role gate

Corporation data requires a Director or CEO role — the ESI corporation
endpoints the app calls need it. The overview page (`/corp`) checks the
main's roles and renders an explanatory state on any failure (missing
role, missing scope, dead token) rather than error spam. Sub-pages
redirect to the overview until the gate passes.

Fixing the gate means one of: setting a Director/CEO character as the
main, re-authorizing the main to grant the roles scope, or re-authorizing
a dead token — the overview says which.

## Corporation assets

The corp-wide asset browser — same region → system → structure grouping,
region and category filters, and per-structure pagination as the
character [assets page](assets.md), without the owner column since
everything belongs to the corporation.

**Offices** get special treatment. Rented offices appear in corp assets
as markers; their contents share a container id that is never itself an
asset row. The browser hides the markers from tables and counts, and
instead renders office contents inside a nested **Office** expander at
the station. Marker-only offices (rented, nothing detected inside) stay
listed.

## Corporation blueprints

The corporation's blueprint inventory — originals with ME/TE, copies
with runs — the same columns as the character page. Locations resolve
through the asset snapshot: blueprints report their location as the
office item id, which hops to the parent station.

## Corporation jobs

Installed corporation industry jobs, active by default with a history
toggle, with installer names resolved from the tracked roster.

## Wallets

A deliberate stub — corporation wallet data isn't surfaced yet.
