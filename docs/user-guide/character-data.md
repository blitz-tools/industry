# Blueprints, skills, and jobs

Three pages under the **Character** nav group cover the industry data
the planner builds on. All three sync in the background and on demand
via the shared **Sync now** button, and all three accept a `?char=`
filter — pick a character from the page's filter to narrow to them; an
unknown id shows every character.

## Blueprints

Everything the registered characters own, original and copy:

- **Original vs copy** badges with the blueprint/copy icons.
- **Material efficiency (ME)** and **time efficiency (TE)** research
  levels on originals.
- **Runs remaining** on copies.
- **Location** — resolved to a real station or structure name where the
  character's data allows it.

These are the rows the planner's owned-blueprint overlay will join
against: which chains can be built today, from which blueprints, sitting
where.

## Skills

The skills page shows overview cards per character, opening into a
per-character skill sheet with:

- **Trained level** — what the character has trained.
- **Active level** — what gameplay math actually sees, including
  implants and boosters.
- **Skill points** per skill, with the total derived and matching ESI's
  reported total.

The distinction matters for the planner: time math should pick
deliberately between trained and active levels when they differ.

## Industry jobs

Installed industry jobs across the characters:

- **Active by default** — what's running now.
- **?all=1** (the history toggle) — completed jobs too.
- Product, activity, status, installer, and location per job.
