"""Assets page tests: grouping, per-type aggregation, filters, fragments,
corp stubs, and the no-ESI-on-render purity guarantee.

All data is seeded directly in the DB — page renders must never touch ESI
(respx routes stay at call_count 0, and respx raises on unmatched calls).
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import respx
from sqlalchemy import select

from app.assets import humanize_sync_age, parse_chars, parse_region
from app.db import utc_now
from app.models import (
    Asset,
    AssetSync,
    Character,
    UniverseLocation,
    UniverseRegion,
    UniverseType,
)
from tests.conftest import token_response

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"
WALLET_URL = "https://esi.test/latest/characters/1234/wallet/"
ASSETS_URL = "https://esi.test/latest/characters/1234/assets/"
STATION_URL = "https://esi.test/latest/universe/stations/6001/"

STATION_JITA = 6001
STATION_AMARR = 6002
RESTRICTED = 7000
SYSTEM_JITA = 3001
SYSTEM_AMARR = 3002
REGION_FORGE = 1001
REGION_DOMAIN = 1002

TYPE_VELDSPAR = 1230
TYPE_ITERON = 1231
TYPE_BLUEPRINT = 9999

ALPHA = 1234  # created via the SSO login flow
BRAVO = 5678


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(
        json=token_response(name="Alpha Pilot")
    )
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _seed_bravo(db_session) -> Character:
    bravo = Character(
        character_id=BRAVO,
        name="Bravo Pilot",
        owner_hash="owner-bravo",
        scopes="publicData esi-assets.read_assets.v1",
        access_token="tok-bravo",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R-bravo",
    )
    db_session.add(bravo)
    await db_session.commit()
    return bravo


def _asset(
    owner_id: int,
    item_id: int,
    type_id: int,
    quantity: int,
    parent: int,
    *,
    flag: str = "Hangar",
    is_blueprint_copy: bool = False,
) -> Asset:
    return Asset(
        owner_type="character",
        owner_id=owner_id,
        item_id=item_id,
        type_id=type_id,
        quantity=quantity,
        location_id=parent,
        location_flag=flag,
        location_type="station",
        parent_location_id=parent,
        is_blueprint_copy=is_blueprint_copy,
        is_singleton=False,
    )


async def _seed_world(db_session) -> None:
    """Two systems in different regions, a shared station, an exclusive
    station, and a restricted structure — plus types and regions."""
    db_session.add_all(
        [
            UniverseType(type_id=TYPE_VELDSPAR, name="Veldspar", volume=0.1),
            UniverseType(type_id=TYPE_ITERON, name="Iteron Mark V", volume=24500.0),
            UniverseType(type_id=TYPE_BLUEPRINT, name="Cruiser Blueprint", volume=0.01),
            UniverseLocation(
                location_id=STATION_JITA,
                kind="station",
                name="Jita IV - Moon 4 - Caldari Navy Assembly Plant",
                system_id=SYSTEM_JITA,
            ),
            UniverseLocation(
                location_id=STATION_AMARR,
                kind="station",
                name="Emperor Family Academy",
                system_id=SYSTEM_AMARR,
            ),
            UniverseLocation(
                location_id=RESTRICTED,
                kind="structure",
                name=f"Structure #{RESTRICTED}",
                restricted=True,
            ),
            UniverseLocation(
                location_id=SYSTEM_JITA,
                kind="solar_system",
                name="Jita",
                system_id=SYSTEM_JITA,
                region_id=REGION_FORGE,
            ),
            UniverseLocation(
                location_id=SYSTEM_AMARR,
                kind="solar_system",
                name="Amarr",
                system_id=SYSTEM_AMARR,
                region_id=REGION_DOMAIN,
            ),
            UniverseRegion(region_id=REGION_FORGE, name="The Forge"),
            UniverseRegion(region_id=REGION_DOMAIN, name="Domain"),
        ]
    )
    db_session.add_all(
        [
            # Alpha in the shared Jita station: two stacks of Veldspar (one
            # merged row), an Iteron, a BPC and a BPO of the same type.
            _asset(ALPHA, 1, TYPE_VELDSPAR, 100, STATION_JITA),
            _asset(ALPHA, 2, TYPE_VELDSPAR, 50, STATION_JITA),
            _asset(ALPHA, 3, TYPE_ITERON, 2, STATION_JITA),
            _asset(ALPHA, 4, TYPE_BLUEPRINT, 1, STATION_JITA, is_blueprint_copy=True),
            _asset(ALPHA, 5, TYPE_BLUEPRINT, 1, STATION_JITA),
            # Bravo in the same station.
            _asset(BRAVO, 6, TYPE_VELDSPAR, 10, STATION_JITA),
            # Alpha-exclusive station in Amarr.
            _asset(ALPHA, 7, TYPE_VELDSPAR, 5, STATION_AMARR),
            # Alpha in the restricted structure.
            _asset(ALPHA, 8, TYPE_ITERON, 1, RESTRICTED),
        ]
    )
    await db_session.commit()


# --- Page render: grouping and filters --------------------------------------


@respx.mock
async def test_assets_page_groups_by_system_and_structure(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)
    await _seed_world(db_session)
    # Rendered pages must not touch ESI; respx raises on unmatched calls.
    wallet = respx.get(WALLET_URL)
    assets = respx.get(ASSETS_URL)

    response = await client.get("/assets")

    assert response.status_code == 200
    assert wallet.call_count == 0
    assert assets.call_count == 0

    text = response.text
    # Systems as plain headers, alphabetical, Unknown system last.
    assert text.index("Amarr") < text.index("Jita") < text.index("Unknown system")
    # Structures under their systems with raw item counts (6 in Jita:
    # Alpha's five stacks + Bravo's one).
    assert "Jita IV - Moon 4 - Caldari Navy Assembly Plant" in text
    assert "6 items" in text
    assert "1 item" in text  # Amarr station
    assert f"Structure #{RESTRICTED}" in text
    # Region names shown next to systems, and offered as filter options.
    assert "The Forge" in text and "Domain" in text
    # Collapsed by default: no asset table rendered on the page itself.
    assert "asset-table" not in text
    # Character Assets is the active nav item.
    assert 'href="/assets" class="active"' in text


@respx.mock
async def test_character_filter_narrows_groups_and_counts(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)
    await _seed_world(db_session)

    alpha_only = await client.get("/assets", params={"chars": str(ALPHA)})
    assert "Emperor Family Academy" in alpha_only.text  # Alpha's Amarr assets
    assert "5 items" in alpha_only.text  # Bravo's stack excluded from Jita

    bravo_only = await client.get("/assets", params={"chars": str(BRAVO)})
    assert "Emperor Family Academy" not in bravo_only.text
    assert "1 item" in bravo_only.text

    # Garbage and unknown ids fall back to all; empty means all.
    garbage = await client.get("/assets", params={"chars": "not-a-number,999999"})
    assert "6 items" in garbage.text


@respx.mock
async def test_region_filter_hides_systems(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)
    await _seed_world(db_session)

    forge = await client.get("/assets", params={"region": str(REGION_FORGE)})
    assert "Jita" in forge.text
    assert "Amarr" not in forge.text
    assert "Unknown system" not in forge.text  # hidden under a region filter

    domain = await client.get("/assets", params={"region": str(REGION_DOMAIN)})
    assert "Amarr" in domain.text
    assert "Jita" not in domain.text

    # Composes with the character filter: Bravo owns nothing in Domain.
    db_session.add(
        AssetSync(
            owner_type="character",
            owner_id=ALPHA,
            status="ok",
            synced_at=utc_now() - timedelta(minutes=5),
        )
    )
    await db_session.commit()
    empty = await client.get(
        "/assets", params={"chars": str(BRAVO), "region": str(REGION_DOMAIN)}
    )
    assert "No assets match the current filters" in empty.text
    # The selected-but-empty region stays visible in the dropdown.
    assert '<option value="1002" selected' in empty.text

    # Unknown region id falls back to all regions.
    unknown = await client.get("/assets", params={"region": "999999"})
    assert "Jita" in unknown.text and "Amarr" in unknown.text


# --- Fragments: aggregation and pagination ------------------------------------


@respx.mock
async def test_fragment_aggregates_per_type(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)
    await _seed_world(db_session)
    station = respx.get(STATION_URL)

    response = await client.get(f"/assets/structure/{STATION_JITA}")

    assert response.status_code == 200
    assert station.call_count == 0  # pure DB read
    text = response.text
    # Two Veldspar stacks from Alpha merge into one row with summed quantity.
    assert "150" in text and "100" not in text.replace("150", "")
    # BPC and BPO of the same type stay separate rows.
    assert text.count("Cruiser Blueprint") == 2
    assert "Copy" in text
    # Ordering: owner name, then type name (Blueprint < Iteron < Veldspar).
    assert text.index("Cruiser Blueprint") < text.index("Iteron Mark V")
    assert text.index("Iteron Mark V") < text.index("Veldspar")
    # Bravo's row follows Alpha's.
    assert text.index("Bravo Pilot") > text.index("Alpha Pilot")
    assert "types" in text  # total row count


@respx.mock
async def test_fragment_paginates_and_carries_filter(client, db_session):
    await _login(client)
    # 60 distinct unresolved types in the Amarr station → two pages at 50.
    rows = [
        UniverseLocation(
            location_id=STATION_AMARR,
            kind="station",
            name="Emperor Family Academy",
            system_id=SYSTEM_AMARR,
        )
    ]
    rows.extend(
        _asset(ALPHA, 10_000 + i, 20_000 + i, 1, STATION_AMARR) for i in range(60)
    )
    db_session.add_all(rows)
    await db_session.commit()

    first = await client.get(f"/assets/structure/{STATION_AMARR}")
    assert first.text.count("<tr>") == 51  # 50 rows + header
    assert "Unknown type #" in first.text  # unresolved names degrade
    assert 'data-page="2"' in first.text

    second = await client.get(
        f"/assets/structure/{STATION_AMARR}", params={"page": 2}
    )
    assert second.text.count("<tr>") == 11  # 10 rows + header
    # Out-of-range pages clamp.
    clamped = await client.get(
        f"/assets/structure/{STATION_AMARR}", params={"page": 99}
    )
    assert clamped.text.count("<tr>") == 11

    # The character filter reaches the fragment and its pagination hrefs.
    filtered = await client.get(
        f"/assets/structure/{STATION_AMARR}", params={"chars": str(ALPHA)}
    )
    assert "chars=1234" in filtered.text


@respx.mock
async def test_fragment_requires_auth(client, db_session):
    await _seed_world(db_session)

    response = await client.get(f"/assets/structure/{STATION_JITA}")

    assert response.status_code == 401  # fetch target: no redirect
    assert "reload" in response.text


@respx.mock
async def test_assets_page_requires_auth(client):
    response = await client.get("/assets")
    assert response.status_code == 302
    assert response.headers["location"] == "/"


# --- Sync button and last-sync display -----------------------------------------


@respx.mock
async def test_manual_sync_forces_and_preserves_filters(client, db_session):
    await _login(client)
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    station = respx.get(
        f"https://esi.test/latest/universe/stations/{STATION_JITA}/"
    ).respond(json={"name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
                    "system_id": SYSTEM_JITA})
    respx.get(f"https://esi.test/latest/universe/systems/{SYSTEM_JITA}/").respond(
        json={"name": "Jita", "constellation_id": 20000020}
    )
    respx.get(
        "https://esi.test/latest/universe/constellations/20000020/"
    ).respond(json={"region_id": REGION_FORGE})
    respx.get(
        f"https://esi.test/latest/universe/regions/{REGION_FORGE}/"
    ).respond(json={"name": "The Forge"})
    respx.get(
        f"https://esi.test/latest/universe/types/{TYPE_VELDSPAR}/"
    ).respond(json={"name": "Veldspar", "volume": 0.1})
    assets = respx.get(ASSETS_URL).respond(
        json=[{
            "item_id": 1,
            "type_id": TYPE_VELDSPAR,
            "quantity": 7,
            "location_id": STATION_JITA,
            "location_flag": "Hangar",
            "location_type": "station",
        }],
        headers={"X-Pages": "1"},
    )

    response = await client.post(
        "/assets/sync",
        data={"chars": str(ALPHA), "region": str(REGION_FORGE)},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/assets?chars={ALPHA}&region={REGION_FORGE}"
    assert assets.call_count == 1
    assert station.call_count == 1  # universe resolution ran

    rows = (await db_session.execute(select(Asset))).scalars().all()
    assert len(rows) == 1 and rows[0].quantity == 7


@respx.mock
async def test_last_sync_humanized_on_page(client, db_session):
    await _login(client)
    db_session.add(
        AssetSync(
            owner_type="character",
            owner_id=ALPHA,
            status="ok",
            synced_at=utc_now() - timedelta(hours=3),
        )
    )
    await db_session.commit()

    response = await client.get("/assets")

    # The apostrophe in "sync'd" is HTML-escaped in the rendered page.
    assert "Data sync&#39;d 3 hours ago" in response.text
    assert "Sync now" in response.text


def test_humanize_sync_age_boundaries():
    now = utc_now()
    assert humanize_sync_age(None) == "Data not synced yet"
    assert humanize_sync_age(now - timedelta(minutes=30), now=now) == (
        "Data sync'd less than an hour ago"
    )
    assert humanize_sync_age(now - timedelta(hours=1), now=now) == (
        "Data sync'd 1 hour ago"
    )
    assert humanize_sync_age(now - timedelta(hours=5), now=now) == (
        "Data sync'd 5 hours ago"
    )
    assert humanize_sync_age(now - timedelta(hours=26), now=now) == (
        "Data sync'd 1 day ago"
    )
    assert humanize_sync_age(now - timedelta(days=3), now=now) == (
        "Data sync'd 3 days ago"
    )


def test_parse_chars_forms():
    def character(cid):
        return Character(
            character_id=cid,
            name=f"Pilot {cid}",
            owner_hash="o",
            scopes="publicData",
            access_token="t",
            access_token_expires_at=utc_now(),
            refresh_token="r",
        )

    valid = [character(1), character(2)]
    assert parse_chars([], valid) is None
    assert parse_chars(["1,2"], valid) == [1, 2]
    assert parse_chars(["1", "2"], valid) == [1, 2]
    assert parse_chars(["2,1,1"], valid) == [1, 2]  # dedup + sort
    assert parse_chars(["garbage", "3"], valid) is None  # unknown ids dropped
    assert parse_region(None) is None
    assert parse_region("1002") == 1002
    assert parse_region("junk") is None


# --- Corporation stubs and nav -------------------------------------------------


@respx.mock
async def test_corp_stub_pages_and_nav_group(client):
    await _login(client)

    assets = await client.get("/corp/assets")
    assert assets.status_code == 200
    assert "Not built yet" in assets.text
    # The nav group is expanded and the right sub-item is active.
    assert 'aria-expanded="true"' in assets.text
    assert 'href="/corp/assets" class="active"' in assets.text

    jobs = await client.get("/corp/jobs")
    assert 'aria-expanded="true"' in jobs.text

    missing = await client.get("/corp/nonexistent")
    assert missing.status_code == 404

    # On character pages the group is collapsed (server-rendered).
    dashboard_wallet = respx.get(WALLET_URL).respond(json=1.0)
    dashboard = await client.get("/dashboard")
    assert 'aria-expanded="false"' in dashboard.text
    assert dashboard_wallet.call_count == 1


@respx.mock
async def test_forget_deletes_asset_rows(client, db_session):
    await _login(client)
    await _seed_bravo(db_session)
    await _seed_world(db_session)
    respx.post("https://sso.test/v2/oauth/revoke").respond(json={})

    response = await client.post(f"/characters/{ALPHA}/forget", follow_redirects=False)

    assert response.status_code == 303
    owners = {
        row.owner_id for row in (await db_session.execute(select(Asset))).scalars()
    }
    assert owners == {BRAVO}
