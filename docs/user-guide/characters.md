# Characters and the roster

## Signing in

EVE SSO is the only login. Signing in sends you to
`login.eveonline.com`; on approval, the app stores your character with
its access and refresh tokens, and background refreshes keep them alive.

## Adding characters

Each pass through **Add character** authorizes one more character. EVE's
SSO screen lets you switch accounts, so characters from multiple EVE
accounts all land in the same roster. The dashboard shows every stored
character with its portrait and wallet balance.

## Re-authorizing

A character needs re-authorization when its refresh token dies or when
the application's scope list changes. The roster's **Re-Auth** button
sends you through SSO again and returns you to the roster; everything
else (tokens, synced data) is untouched. Characters holding a dead
refresh token show an out-of-sync state and get skipped by data syncs
until re-authorized.

## The roster

The roster (under the **Character** nav group) shows one card per
character with its corporation, alliance, current location, and skill
queue, plus the sync-state portrait ring — ok, stale, never-synced, or
error — that reflects the background data syncs.

Each card also carries a **Plan-eligible** line: how many of the active
plans' nodes that character holds the skill gates for (against their
current skill sheets) — counted only over the plans they were planned
into, since a plan's participant pool is pinned at render time and a
non-participant cannot be assigned to it regardless of skills. Cards
outside every active pool read "not in an active plan's pool", and
with no active plans at all the line says so. It is the
assignment-eligibility picture — who could install what — ahead of the
job-allocation surfaces that assign the work.

Below the metadata block, participants in active plans get one linked
row per plan — the target's commodity icon beside the plan name,
through to the plan's detail page.

Card actions:

- **Set as main** — flags the character as the main (see below).
- **Re-Auth** — re-authorization (also used to grant newly registered
  scopes).
- **Forget** — removes the character and its synced data.

## The main character

One character is flagged as the **main**. The main character determines
which corporation the **Corporation** section targets (see
[Corporation](corporation.md)); switching mains switches the targeted
corp, and the old corporation's data stays in the database, untargeted.

The main must hold the **Director** or **CEO** role in its corporation
for the Corporation section to function.
