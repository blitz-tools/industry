# Installation

The application is a small FastAPI service with an SQLite database. The
supported deployment is a container: the only host requirements are `uv`
(to build the image) and a container runtime with compose — `podman
compose` on Fedora (Docker-compatible runtimes work as well).

## Register an EVE application

The app authenticates exclusively through EVE Online SSO, so it needs an
application registered on the EVE developers portal:

1. Create an application at
   <https://developers.eveonline.com>.
2. Callback URL: `http://localhost:8000/auth/eve/callback` — it must
   match `ESI_CALLBACK_URL` byte-for-byte (localhost ≠ 127.0.0.1; no
   trailing slash). For a public deployment use your `https://` URL and
   update `.env` to match.
3. Select the scopes listed in `.env.example` (`ESI_SCOPES`). The
   requested scopes must be a subset of the registered scopes or SSO
   rejects the authorization.
4. Copy the Client ID and Client Secret into `.env`.

!!! note
    Changing the scope list later — on the portal or in `.env` — requires
    every existing character to re-authorize before the new scopes take
    effect.

## Environment

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)
```

The full variable set:

| Variable | Purpose |
|---|---|
| `ESI_CLIENT_ID` / `ESI_CLIENT_SECRET` | SSO application credentials |
| `ESI_CALLBACK_URL` | Must match the portal registration byte-for-byte |
| `ESI_SCOPES` | Space-separated OAuth scopes (see `.env.example`) |
| `SECRET_KEY` | Session cookie signing key (`openssl rand -hex 32`) |
| `ESI_USER_AGENT` | Contact address for CCP's best practices |
| `BASE_URL` | Public base URL of the deployment (no trailing slash) |
| `DATABASE_URL` | SQLAlchemy async URL; SQLite by default |

## Run it

```sh
podman compose up --build      # or: docker compose up --build
```

The image is multi-stage: the default (production) target ships only
runtime dependencies and the app code. The SQLite database lives in
`./data/` (bind-mounted to `/data` in the container) and survives
restarts. Migrations run automatically on start.

Open the app (for example <http://localhost:8000>), sign in through EVE
SSO, and you should land on the dashboard with your character's portrait
and wallet balance — proving the full OAuth code → token → ESI call
chain.

## First steps after startup

1. **Set the database location** if you want something other than the
   default SQLite file (`DATABASE_URL`).
2. **Import the SDE** — blueprint recipes come from the EVE static data
   export, and the initial import is the administrator's call. See
   [SDE data](sde-data.md).
3. **Add your characters** — see the
   [user guide](../user-guide/characters.md).

## SQLite, Postgres, and backups

The default database is SQLite via SQLAlchemy + Alembic, swappable to
Postgres later by changing `DATABASE_URL`. Back up the database file (and
`data/` in container deployments) on whatever schedule suits you — the
database holds characters, tokens, synced game data, and the SDE mirror.
Everything in it can be re-synced from EVE except the user-managed state
(main character flag, any future build plans).
