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

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)

uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000>, sign in, and you should land on the dashboard
with your character's portrait and wallet balance — proving the full
OAuth code → token → ESI call chain.

### Tests

```sh
uv run pytest
uv run ruff check .
```

## Docker

```sh
docker compose up --build
```

The SQLite database lives in `./data/` (bind-mounted to `/data` in the
container) and survives restarts. Migrations run automatically on start.

## Security notes

- This is a **personal tool**: anyone who can reach the app and logs in with
  their own EVE account can see all stored characters. Keep it on localhost
  or behind an access restriction (VPN, reverse-proxy auth) when deployed.
- The session cookie is signed with `SECRET_KEY`; tokens never leave the
  database.
