# Architecture

## Three data layers

Every feature is a join across exactly these layers. Keeping the split
crisp is what lets T2/T3 invention and reactions arrive later as *data
and resolver extensions* instead of schema rewrites.

| Layer | Source | Nature | Examples |
|---|---|---|---|
| **Static (recipes)** | EVE SDE, imported | Write-once per release | blueprint → materials, products, required skills, activity durations |
| **Dynamic (world state)** | ESI, ETag-cached sync | Refreshed in background | owned blueprints (ME/TE/runs), skills, industry jobs, assets |
| **User state** | This app | User-managed CRUD | main character, structures, build plans |

Two consequences worth stating outright:

- **ESI cannot answer "what does this blueprint build from."** The
  production chain lives in the SDE. ESI supplies what the SDE can't:
  which blueprints you own, who you are, what's installed, where things
  sit, and what it costs.
- **The schema models all industry activities from day one** —
  manufacturing, copying, invention, reactions, and T3 reverse
  engineering — via a generic activity dimension. V1 resolves the T1
  manufacturing + reaction chain; invention/T2 and T3 land incrementally
  without migrations that retrofit activity types.

## The SDE mirror

The `sde_*` namespace is a verbatim mirror of the fuzzwork SQLite dump —
no alembic migration, no ORM models, drop-and-recreate per release.
Interpreting the data (joins, dedup, labels) belongs to the consuming
query layer, never the import. See [SDE data](../admin/sde-data.md).

That query layer is the catalog section of `app/industry.py` (M2):
commodity search and recipe reads as raw SQL over the mirror, plus the
owned-blueprint overlay joining the live `blueprints` rows. Its
recorded interpretation rules: catalog membership is the products of
manufacturing and reactions (activity ids 1 and 11 — the dump files
reaction recipes under 11 even though `ramActivities` labels reactions
9); the SDE name is authoritative, with `universe_types` naming only
ids the dump lacks; and a product's producer is its first
`industryActivityProducts` row preferring published blueprints (the
dump carries unpublished CCP test artifacts that can sit first).

The same seam runs through job correlation (M6): ESI reports reaction
jobs under activity 9 while the mirror files reaction recipes under
11, so the matcher reconciles 9→11 (pinned in `app/plans.py`) when
claiming synced jobs into build plans. The claim itself is heuristic —
blueprint type plus reconciled activity, filtered by the node's pinned
facility location only when that structure has a sighting location
(hand-entered structures match loosely), and floored at the plan's
creation time. One job claims into at most one plan across all plans;
false positives are accepted by design.

The Purchase⇄Build marking (M6) leans on a plan-domain invariant
instead: a plan's raw-material totals are always recomputable from its
nodes' snapshotted demands (`materials_json`), so marking a node
Purchase amends the acquisition table by recompute — the demands of
the nodes the current markings still need, per a backward
reachability walk from the target (`necessary_nodes`) — which makes
un-marking symmetric and the amendment idempotent. Suppliers only a
purchased node consumed turn unnecessary and drop out entirely
(greyed in the tree and chain strip, never blocking completion);
suppliers shared with still-built nodes keep their full planned
quantities in v1, because re-deriving a chain around a local change
is the wave model's job (M9), never a local patch.

## Sync machinery

- **Owner-keyed tables**: `assets`, `blueprints`, `industry_jobs`, and
  their sync-status records carry `owner_type`/`owner_id`, so
  corporation data reuses the character machinery unchanged.
- **Per-kind sync status**: each data kind (character blueprints, skills,
  jobs; corp assets, blueprints, jobs) has its own scope gate and
  recorded outcome, rendered as sync-state indicators on the pages.
- **ESI client**: ETag-cached GETs with per-character token refresh,
  rate-limit handling, and scope-gated calls only — scopeless calls are
  guaranteed 403s and burn ESI's error-limit budget.
- **Universe resolver**: type, location, and structure names resolve at
  sync time through a write-once cache; location ids that arrive without
  a usable type classify by id range (stations below 10¹² answer on the
  public stations endpoint, structures above it on the scoped structures
  endpoint) and park as restricted when unresolvable.

## Page-render purity

Page renders never touch ESI. Everything the pages show resolves through
the background syncs into database tables first; views are pure database
reads. This keeps page loads fast and predictable, and keeps ESI failure
modes out of the rendering path.
