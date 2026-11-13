# industry

Web application interfacing with the [EVE Online ESI API](https://esi.evetech.net/).
Currently a scaffold implementing EVE SSO authorization — the foundation for a
future asset manager and industry planner.

## How it works

- **EVE SSO is the only login.** There are no local accounts. Signing in sends
  you to `login.eveonline.com`; on approval the app stores your character with
  its access and refresh tokens.
- **Multiple characters, multiple EVE accounts.** Each pass through "Add
  character" authorizes one more character (EVE's SSO screen lets you switch
  accounts). The dashboard shows every stored character, and background token
  refreshes work for all of them.
- **SQLite** stores characters and tokens (via SQLAlchemy + Alembic, swappable
  to Postgres later).

## Register an EVE application

1. Create an application at <https://developers.eveonline.com>.
2. Callback URL: `http://localhost:8000/auth/eve/callback` — it must match
   `ESI_CALLBACK_URL` byte-for-byte (localhost ≠ 127.0.0.1; no trailing slash).
   For a public deployment use your `https://` URL and update `.env`.
3. Select the scopes listed in `.env.example` (`ESI_SCOPES`). Changing scopes
   later requires re-authorization.
4. Copy the Client ID and Client Secret into `.env`.

## Local development

Development and testing run inside a local container — no local dependency
installs. The only host requirements are `uv` (to build) and a container
runtime with compose (`podman compose` on Fedora, or `docker compose`).

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)

podman compose -f compose.dev.yml up dev
```

Open <http://localhost:8000>, sign in, and you should land on the dashboard
with your character's portrait and wallet balance — proving the full
OAuth code → token → ESI call chain.

How it works:

- The repo is bind-mounted at `/app` inside the container, so code edits
  pick up immediately via `--reload` — no rebuild needed.
- All dependencies (including dev tools) are baked into the image's `dev`
  stage with the venv at `/opt/venv`; rebuild with
  `podman compose -f compose.dev.yml build dev` only after changing
  `pyproject.toml` or `uv.lock`.
- The dev database is `industry.db` at the repo root, shared with the
  pre-container workflow — authorized characters carry over.
- Under rootless podman, the container runs as root mapped to your user,
  so files it writes into the mount (caches, the DB) keep host ownership.

### Tests, lint, migrations

All inside the same container:

```sh
podman compose -f compose.dev.yml run --rm dev pytest
podman compose -f compose.dev.yml run --rm dev ruff check .

# migration cycle against a throwaway database
podman compose -f compose.dev.yml run --rm dev sh -c \
  'DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic downgrade base && \
   DATABASE_URL=sqlite+aiosqlite:////tmp/mig.db alembic upgrade head'
```

### Direct uv alternative

The container is the supported path, but the plain-uv workflow still works
if a container runtime is unavailable: `uv sync`, then `uv run` for the
commands above.

## Docker

```sh
docker compose up --build      # or: podman compose up --build
```

The image is multi-stage: the default (production) target ships only
runtime dependencies and the app code; the `dev` target used by
`compose.dev.yml` adds the dev toolchain. The SQLite database lives in
`./data/` (bind-mounted to `/data` in the container) and survives restarts.
Migrations run automatically on start.

## Security notes

- This is a **personal tool**: anyone who can reach the app and logs in with
  their own EVE account can see all stored characters. Keep it on localhost
  or behind an access restriction (VPN, reverse-proxy auth) when deployed.
- The session cookie is signed with `SECRET_KEY`; tokens never leave the
  database.
