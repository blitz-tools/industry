# Security

## The personal-tool model

This is a **personal tool**: anyone who can reach the deployment and logs
in with their own EVE account can see **all** stored characters and their
data. There are no local user accounts and no per-user separation — EVE
SSO is an identity check, not an access boundary.

Keep the app on localhost, or put an access restriction in front of it
when deployed:

- a VPN (WireGuard, Tailscale, …), or
- authentication at a reverse proxy.

Exposing it directly to the internet means anyone with an EVE account can
browse your corporation's data.

## Tokens and sessions

- The session cookie is signed with `SECRET_KEY`; tokens never leave the
  database.
- Access and refresh tokens are stored per character and refreshed in the
  background. Rotating `SECRET_KEY` invalidates all sessions (users just
  sign in again); it does not affect stored tokens.
- The EVE SSO application's registered scopes must cover every scope in
  `ESI_SCOPES`, and changing the set requires each character to
  re-authorize.

## ESI error-budget discipline

The application deliberately never makes ESI calls that are guaranteed to
fail:

- Endpoint calls are scope-gated — a call isn't attempted unless the
  character holds the required scope, because scopeless calls are
  guaranteed 403s and burn ESI's error-limit budget.
- Structures your characters can't dock in are *parked* as
  `Structure #<id>` and retried only after a multi-day cooldown, instead
  of hammered.
- The same philosophy governs the corporation role gate: a non-Director
  main renders an explanatory state rather than error spam.
