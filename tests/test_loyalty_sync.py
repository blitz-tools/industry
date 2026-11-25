"""The char-loyalty sync kind (M6): wholesale replace semantics and the
per-kind status record. The happy path, the scope gate, and the
dead-token short-circuit ride the shared per-character pass and are
covered in tests/test_character_data.py."""

from datetime import timedelta

import httpx
import respx
from sqlalchemy import select

from app.db import utc_now
from app.esi.assets import sync_all_characters
from app.esi.universe import UniverseResolver
from app.models import Character, CharacterLoyalty, DataSync
from tests.conftest import TEST_SETTINGS

ALPHA = 1234
ASSETS_URL = f"https://esi.test/latest/characters/{ALPHA}/assets/"
LOYALTY_URL = f"https://esi.test/latest/characters/{ALPHA}/loyalty/points/"
LP_CORP = 1000001
LP_OTHER_CORP = 1000003

GRANT = "publicData esi-assets.read_assets.v1 esi-characters.read_loyalty.v1"

# The per-character pass's kind order: assets, blueprints, skills,
# loyalty, jobs — the kinds without scopes never touch their endpoints.
LOYALTY_OUTCOME_INDEX = 3


def _character() -> Character:
    return Character(
        character_id=ALPHA,
        name="Alpha Pilot",
        owner_hash="owner-alpha",
        scopes=GRANT,
        access_token="tok",
        access_token_expires_at=utc_now() + timedelta(minutes=30),
        refresh_token="R",
    )


def _make_esi(app, db_session):
    from app.esi.client import ESIClient

    return ESIClient(
        app.state.http, TEST_SETTINGS, db_session,
        clock=app.state.esi_clock, limiter=app.state.esi_limiter,
        jitter=lambda: 0.0,
    )


def _mock_pass_endpoints(balances_side_effect=None):
    """The endpoints the scoped kinds hit: empty assets, and loyalty per
    the test's responses. Corporations named by the balances get name
    routes (the sync's best-effort cache pass)."""
    respx.get(ASSETS_URL).respond(json=[], headers={"X-Pages": "1"})
    if balances_side_effect is not None:
        return respx.get(LOYALTY_URL).mock(side_effect=balances_side_effect)
    return respx.get(LOYALTY_URL).respond(json=[])


def _mock_corp_names(*corporation_ids: int):
    for corporation_id in corporation_ids:
        respx.get(f"https://esi.test/latest/corporations/{corporation_id}/").respond(
            json={"name": f"Corporation {corporation_id}"}
        )


@respx.mock
async def test_loyalty_replaces_wholesale(app, db_session):
    """A repeat sync with changed balances replaces the snapshot: spent
    balances drop, changed ones update — no stale rows survive."""
    character = _character()
    db_session.add(character)
    await db_session.commit()
    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    _mock_corp_names(LP_CORP, LP_OTHER_CORP)

    route = _mock_pass_endpoints(
        [
            httpx.Response(
                200, json=[{"corporation_id": LP_CORP, "points": 200_000}]
            ),
            httpx.Response(
                200,
                json=[
                    {"corporation_id": LP_CORP, "points": 150_000},
                    {"corporation_id": LP_OTHER_CORP, "points": 500},
                ],
            ),
        ]
    )

    await sync_all_characters(db_session, esi, [character], resolver=resolver)
    await sync_all_characters(db_session, esi, [character], resolver=resolver)

    assert route.call_count == 2
    rows = {
        row.corporation_id: row
        for row in (
            await db_session.execute(
                select(CharacterLoyalty).where(
                    CharacterLoyalty.character_id == ALPHA
                )
            )
        ).scalars()
    }
    # The first sync's exact balance is gone; the second's rows stand.
    assert rows[LP_CORP].points == 150_000
    assert rows[LP_OTHER_CORP].points == 500
    sync = await db_session.get(DataSync, ("char-loyalty", "character", ALPHA))
    assert sync.status == "ok"


@respx.mock
async def test_loyalty_empty_balances_clear_the_table(app, db_session):
    """ESI returns only corporations with a balance: an empty list means
    the character spent everything, and the snapshot clears."""
    character = _character()
    db_session.add(
        CharacterLoyalty(character_id=ALPHA, corporation_id=LP_CORP, points=200_000)
    )
    db_session.add(character)
    await db_session.commit()
    esi = _make_esi(app, db_session)
    resolver = UniverseResolver(db_session, esi, settings=TEST_SETTINGS)
    _mock_pass_endpoints()

    outcomes = await sync_all_characters(
        db_session, esi, [character], resolver=resolver
    )

    assert outcomes[LOYALTY_OUTCOME_INDEX].status == "synced"
    assert outcomes[LOYALTY_OUTCOME_INDEX].item_count == 0
    rows = (
        (
            await db_session.execute(
                select(CharacterLoyalty).where(
                    CharacterLoyalty.character_id == ALPHA
                )
            )
        )
        .scalars()
        .all()
    )
    assert rows == []
    sync = await db_session.get(DataSync, ("char-loyalty", "character", ALPHA))
    assert sync.status == "ok"
