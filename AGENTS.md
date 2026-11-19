# AGENTS.md — session entry map

How to start a new session in this repo: which documents govern which kind
of work, and how information flows between them. The SDLC itself (human
product owner, AI junior developer, review before merge) is described in the
root README — this file doesn't repeat it, it routes you.

## Session types

Match the session to the work, and read the entry documents before doing
anything else.

### Design / mockup iteration

Working on the build planner wireframes in `design/` — per-chain sets
(`typhoon/`, `charon/`, …) plus shared styles in `design/shared/`.

- **Read first**: `design/README.md` (the layout and the binding mockup
  convention — the Typhoon set is the reference standard; new chains get
  the same pages and visuals with different data), then the target set's
  README (data provenance) and `design/typhoon/ITERATION.md` (the working
  review document: settled decisions, recommendations awaiting a
  product-owner call, polish worklist).
- **Context inputs** (read-only for these sessions): `MILESTONES.md` (what
  each mockup section maps to) and the matching
  `reference/chains/<TARGET>-CHAIN.md` chain document.
- **Output**: edits to the target set's mockup HTML, shared CSS in
  `design/shared/`, and updates to `ITERATION.md`.
  This work stays in its own session — it does not touch app code.
- **Graduation rule**: when a design decision settles, it moves to its
  durable home — milestone-affecting vocabulary and behavior go into
  `MILESTONES.md`, then the entry is removed from `ITERATION.md`. The
  working document shrinks as it is consumed; it is not an archive.

### Planner implementation (M2 onward)

Building the app surfaces described by the milestones.

- **Read first**: `MILESTONES.md` (roadmap and recorded decisions),
  `TODO.md` (small items and ideas).
- **Reference material**: `reference/README.md` (chain-resolution and
  timeline formula reference — the math the planner implements),
  `reference/chains/TYPHOON-CHAIN.md` (golden values to check
  against), `docs/development/` (architecture, testing, workflow).
- `app/industry.py` is the module the planner query layer grows in.

### Reference / model work

Maintaining the chain-expansion and timeline models.

- **Read first**: `reference/README.md`.
- `reference/chain_expand.py` and `reference/timeline_model.py` are the
  source of the golden values; regenerating updates `reference/chains/TYPHOON-CHAIN.md`.

### Documentation site

Working on the published docs.

- **Read first**: `mkdocs.yml` and `docs/`.
- The site is Zensical (not Material for MkDocs — see `docs/` dependency
  group and the CI `Lint docs & config` job).
- `design/` is deliberately outside the site and must stay there:
  the mockups contain live character and corporation names.

### CI / repo infrastructure

Working on workflows, rulesets, lint config.

- `.github/workflows/` (ci.yml, codeql.yml, docs.yml), `.pymarkdownlnt.yml`,
  `.yamllint`. `main` is ruleset-protected with required checks; everything
  lands through PRs.

## Document map and information flow

```text
MILESTONES.md          vision / roadmap (durable, decisions of record)
TODO.md                small items and ideas
        |
        | informs
        v
design/                working design artifacts (per-chain wireframe sets
  + shared/            plus shared styles; typhoon/ is the reference set)
  + ITERATION.md       working decisions doc (consumed as decisions settle)
        |
        | settled decisions graduate back to MILESTONES.md
        v
reference/             formula models (chain expansion, timelines)
        |  regenerates
        v
reference/chains/      golden values per chain (durable, machine-generated)
  TYPHOON-CHAIN.md     the standing Typhoon validation case; more chains
                       added as simulation targets
        |
        | check-against output
        v
app/ + docs/           implementation and published documentation
```

## Working-document hygiene

- Working and session material (e.g. `design/typhoon/ITERATION.md`,
  kept with its set) is indexed from this file, **not** from the
  READMEs of the artifacts it works on. Artifact READMEs describe the
  artifact; this file routes sessions.
- A working document has a termination condition, not an archive role:
  once its content is settled, it graduates to the durable document and
  the entry is removed.
- Anything that must not reach the published site (live character or
  corporation names) stays out of `docs/` — `design/` is the
  sanctioned home for that material.
