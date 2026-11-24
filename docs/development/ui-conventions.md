# UI conventions

The patterns and rules settled on the structures page (M3, twelve
review rounds, 2026-11-23). New pages follow these so the app stays
consistent as the planner surfaces land — the same way the mockups'
binding convention holds every chain set to the Typhoon reference,
this page binds every app surface to the structures page. (The mockup
convention itself lives in `design/README.md`, deliberately outside
this site — it contains live character and corporation names.)

## Styling: the mockups are the source of truth

`design/shared/mockups.css` is the design system;
`app/static/style.css` carries the ported shared library. Rules:

- **Port components verbatim** from mockups.css — never restyle from
  memory. The first structures pass re-invented badges, chips, and
  autocomplete with wrong values; every divergence was visible.
- **The mockups' `.var` cyan highlight is mockup-only** (owner
  direction, 2026-11-23): it marks computed values for design review
  and never ships — the app does not visually mark computed vs static
  content. Do not port it; templates carry no `.var` spans.
- When a page uses a class the app doesn't style yet, **port it** —
  several classes shipped unstyled (`card-sub`, `sync-source`,
  `muted`) because nothing checked.
- **Measure, don't eyeball**: render both pages in headless Chrome and
  extract geometry (grid columns, field positions) when aligning
  layout. The app's content width was 72rem against the mockups' 84rem
  — invisible in code, obvious in a column count.
- Planner-specific components (meters, wave bars, phase rows) stay in
  mockups.css until their consuming milestone ports them.

Chrome values of record: `.content` max-width **84rem**; form grids
use proportional columns when a field needs width (activity chips on
one line) with an `auto-fit` fallback below 78rem.

## Chip groups

Radio inputs labeled as `.chip-button` pills:

- Radios for keyboard navigation; **a second click unchecks** a
  selected chip (radios can't natively — track `data-was-checked`).
- The server renders the initial `selected` class, but the JS **owns
  chip styling from the first interaction**: it must move or clear
  with the checked radio, or the default chip stays styled forever.
- Chips **lock** (disable + dim) when their value derives from
  something else — the security chips lock to a picked system's class.
  Locking is UX; the server stays authoritative on save.

## Forms

- **One form, multiple states**: create, edit, and add-a-related-thing
  are the same form in different query-param states, one POST handler.
- Detail panels **hide until an entry point asks** (`?form=add`, an
  edit link, an import) — and carry `#anchor` fragments (or
  post-swap `scrollIntoView`) so the reveal lands in view.
- Link query params must **match route parameter names exactly** — a
  `?structure=` link against a `structure_id` parameter silently
  renders a blank form (this shipped).
- Numeric fields are `type="number"` with `min`/`max`/`step`
  (two-decimal tax: `step="0.01"`); the server parses and validates
  regardless — client controls never gate integrity.
- Validation errors re-render the form (422) with the submitted
  values echoed and the panel forced visible.

## In-place updates (no full refreshes)

The assets-page pattern, generalized on structures:

- Links and form posts fetch and **replace `<main>`'s children**,
  `pushState` the URL, and re-bind via `window.initXxxPage()` —
  swapped markup carries no executable scripts.
- **Once-only wiring** (document-level listeners, popstate) is guarded
  by a `window` flag outside the init function; listeners inside the
  init re-query elements **at event time** so they survive swaps
  without piling up.
- Confirmations use a **native `<dialog>`** (`showModal`,
  `::backdrop`, Escape/backdrop close) — never the browser
  `confirm()` popup. The pending action is stored; Confirm submits it
  through the swap path.
- Any fetch failure falls back to full navigation.
- **Multi-page flows share one JS file** (the planner's entry and plan
  pages): each page's init is a no-op when its elements are absent,
  and one `swapMain` calls every init after a swap — dispatch on
  element presence, never on the URL (pushState and swaps can disagree
  mid-flight).

## URL-state pages (the planner pattern)

Pages whose whole input set is query params (the planner, until M6
persists plans):

- **Absence means default**: params are omitted when they equal the
  registry/roster default (a `?manufacturing=` appears only when it
  overrides), so a default change re-resolves honestly instead of
  pinning stale links. Never serialize the default; always serialize
  an explicit choice.
- **Absent vs empty are different states** for list params: `p`
  missing = the default participant pool; `?p=` present-but-empty =
  an explicit empty pool. Parse from `request.query_params` — FastAPI's
  typed list params cannot express the empty sentinel.
- The server re-renders on every interaction (the stepper, toggles,
  and selects rebuild the URL and swap) — the client never computes
  derived values, it only constructs the next URL.
- Invalid ids (a stale target, an unknown registration) degrade to the
  default or redirect — never a 500, never trust link construction.

## Page purity and ESI

Page renders never touch ESI. ESI calls are allowed **at save time**
and in **action-triggered JSON endpoints** (the system type-ahead
resolves each suggestion's security through the ETag-cached public
client; the roster's per-card fetches are the older precedent). An
unreachable ESI degrades — never blocks — the flow.

## Template gotchas (both shipped as bugs)

- **`tojson` in an HTML attribute needs single quotes**:
  `data-x='{{ x | tojson }}'`. Jinja's tojson escapes `<>&'` but not
  `"` — double-quoted attributes break mid-JSON and the script dies
  at `JSON.parse`.
- **Content between blocks in a child template is silently dropped**
  by Jinja — markup must live inside a block (a dialog vanished until
  moved inside `{% block content %}`).

## Database lesson

SQLAlchemy batches same-table updates into one `executemany` **ordered
by primary key** — code order between two UPDATEs means nothing. When
a demote-then-promote pair must satisfy a partial unique index, put a
`flush()` barrier between them; pin it with a test whose ids sort the
wrong way (the crash only fired when the promoted row's id was lower).

## Verification

- Server behavior: pytest through the ASGI client (SSO login mocked
  via respx; ESI endpoints mocked with per-test routes).
- Browser behavior: the **headless-Chrome harness** — dump the
  authenticated page (a session cookie minted with the app's own
  secret), inject a script that drives the real JS and records
  results into a `data-` attribute, run `--headless=new --dump-dom`,
  parse the attribute. Harness gotchas: escape `</script>` inside
  embedded page JSON, and stub `fetch` selectively — a blanket stub
  feeds dev-reload's version poller a fake response and it reloads
  the pushed URL.
