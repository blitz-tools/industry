# Getting started

Development and testing run inside a local container — no local
dependency installs. The only host requirements are `uv` (to build) and a
container runtime with compose — `podman compose` on Fedora
(Docker-compatible runtimes work as well).

```sh
cp .env.example .env
# fill in ESI_CLIENT_ID, ESI_CLIENT_SECRET, SECRET_KEY (openssl rand -hex 32)

podman compose -f compose.dev.yml up dev
```

Open <http://localhost:8000>, sign in, and you should land on the
dashboard with your character's portrait and wallet balance.

## How the dev container works

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
- The SELinux label issue on Fedora needs `security_opt: label=disable`
  on the bind mount (already in `compose.dev.yml`).

## Browser auto-reload

The dev compose file sets `DEV_AUTO_RELOAD`: open browsers poll a version
token and refresh themselves when source files change. It needs one
manual reload to activate.

While actively iterating, `touch .dev-reload-paused` in the repo root
holds browser reloads (for example, while mid-edit across several files);
`rm` it to resume. CI pins the flag off.

## Direct uv alternative

The container is the supported path, but the plain-uv workflow still
works if a container runtime is unavailable: `uv sync`, then `uv run` for
the commands in [testing](testing.md).

## Docs site

The documentation you are reading builds with the `docs` dependency
group (Zensical, in MkDocs compatibility mode — see
[testing](testing.md) for the tooling notes):

```sh
podman compose -f compose.dev.yml run --rm dev \
  uv run --group docs zensical serve    # live preview
```

Use `zensical build --strict` to verify a build (the same check CI runs
on every PR) without serving.
