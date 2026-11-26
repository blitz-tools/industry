"""LP acquisition + roster eligibility surfaces (M6 PR 9): the curated
LP_OFFERS pin read through character_loyalty — the "BPCs — LP front"
gating flavor on an LP-sourced, unowned target blueprint, the LP
acquisition table (offer-store rows sufficient / short, wrong-currency
rows visible but unusable) on the fresh planner page and the plan
detail, and the roster's assignment-eligibility line. The loyalty sync
itself is tests/test_loyalty_sync.py; these are the read surfaces it
feeds."""

from urllib.parse import parse_qs, urlparse

import respx

from app.models import CharacterLoyalty, UniverseCorporation
from app.plans import LPOffer
from tests.conftest import mock_roster_metadata, token_response
from tests.test_planner_chain import chain_db  # noqa: F401  (fixture)
from tests.test_planner_plan import (  # noqa: F401  (fixture)
    CORP_MEMBER,
    MAIN,
    OUT_OF_CORP,
    planner_db,
)

# The fixture's self-referential structure array: its blueprint (4201)
# is in no pool, so a chain targeting it carries exactly the
# LP-flavored gating the TFI shape describes.
ASSEMBLY = 4200
ASSEMBLY_BP = 4201
TYPHOON = 644

# The test offer store (a TLF stand-in) and a wrong-currency
# corporation the participants hold wealth at.
STORE = 7000
WRONG_STORE = 8000

SSO_TOKEN_URL = "https://sso.test/v2/oauth/token"


def _pin_test_offers(monkeypatch):
    """Point the curated pin at the fixture's unowned blueprint with the
    TFI store's variant shape: a 10-pack and a single."""
    monkeypatch.setattr(
        "app.plans.LP_OFFERS",
        (
            LPOffer(
                STORE, ASSEMBLY_BP, "10-pack", 200_000, 200_000_000,
                ((12345, "Test Package", 8),), 10,
            ),
            LPOffer(
                STORE, ASSEMBLY_BP, "Single", 100_000, 20_000_000, (), 1,
            ),
        ),
    )


async def _seed_loyalty(db, *rows: tuple[int, int, int]):
    """Loyalty balances (character, corporation, points) plus the
    universe name cache rows the table labels sources from."""
    for character_id, corporation_id, points in rows:
        db.add(
            CharacterLoyalty(
                character_id=character_id,
                corporation_id=corporation_id,
                points=points,
            )
        )
    db.add(UniverseCorporation(corporation_id=STORE, name="Test Militia"))
    db.add(UniverseCorporation(corporation_id=WRONG_STORE, name="Paragon Wealth"))
    await db.commit()


async def _login(client):
    respx.post(SSO_TOKEN_URL).respond(json=token_response())
    response = await client.get("/auth/eve/login", follow_redirects=False)
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    await client.get("/auth/eve/callback", params={"code": "abc", "state": state})


async def _export(client, target: int, qty: int = 10) -> int:
    response = await client.post(
        "/plans", data={"target": target, "qty": qty}, follow_redirects=False
    )
    assert response.status_code == 303
    return int(response.headers["location"].rsplit("/", 1)[1])


def _mock_roster_esi():
    """The roster page's per-character metadata for every fixture
    character (the main's routes come from the shared mock; the
    corp-mate and the outsider need their own wallet/public-info
    routes — their grants predate the location/skillqueue scopes)."""
    respx.get("https://esi.test/latest/characters/1234/wallet/").respond(
        json=4321.5
    )
    mock_roster_metadata()
    for character_id, corporation_id in (
        (CORP_MEMBER, 98000001),
        (OUT_OF_CORP, 99000002),
    ):
        respx.get(
            f"https://esi.test/latest/characters/{character_id}/wallet/"
        ).respond(json=100.0)
        respx.get(
            f"https://esi.test/latest/characters/{character_id}/"
        ).respond(json={"corporation_id": corporation_id})
    respx.get("https://esi.test/latest/corporations/99000002/").respond(
        json={"name": "Other Corp"}
    )


@respx.mock
async def test_fresh_plan_lp_gating_and_table(client, chain_db, monkeypatch):  # noqa: F811
    """An LP-sourced target with nothing owned gates with the currency
    flavor, and the acquisition table tells the LP story: the pooled
    balance at the offer store with its per-character breakdown, the
    best variant as the path, sufficient status. Wrong-currency rows
    stay hidden in v1 — even real wealth at a corporation without an
    offer is not an actionable path (the owner review call; they
    return when there is a balance story worth showing)."""
    await _login(client)
    _pin_test_offers(monkeypatch)
    await _seed_loyalty(
        chain_db,
        (MAIN, STORE, 150_000),
        (CORP_MEMBER, STORE, 250_000),
        (MAIN, WRONG_STORE, 632_000),
    )

    response = await client.get(
        "/planner/plan", params={"target": ASSEMBLY, "qty": 10}
    )
    assert response.status_code == 200
    assert "BPCs — LP front" in response.text
    assert "blueprint not owned" not in response.text
    # The table: source, pooled balance, breakdown, path, status.
    assert "LP acquisition — Test Assembly Array Blueprint" in response.text
    assert "Test Militia" in response.text
    assert "Test Pilot 150,000" in response.text
    assert "Corp Mate 250,000" in response.text
    assert "1× 10-pack" in response.text
    assert "200,000 LP" in response.text
    assert "sufficient" in response.text
    # Wrong-currency wealth stays hidden — real balance, no offer.
    assert "Paragon Wealth" not in response.text
    assert "632,000" not in response.text
    assert "no offer at this store" not in response.text


@respx.mock
async def test_fresh_plan_without_offers_keeps_plain_gating(client, chain_db):  # noqa: F811
    """No pinned offer for the blueprint: the plain gating text stands
    and the LP section stays hidden."""
    await _login(client)

    response = await client.get(
        "/planner/plan", params={"target": ASSEMBLY, "qty": 1}
    )
    assert response.status_code == 200
    assert "blueprint not owned" in response.text
    assert "BPCs — LP front" not in response.text
    assert "LP acquisition" not in response.text


@respx.mock
async def test_plan_detail_lp_table_tracks_shortfall(client, chain_db, monkeypatch):  # noqa: F811
    """The detail page's table renders from live loyalty for the PINNED
    participants: the pooled balance short against the best variant's
    cost reads as 'short N LP'."""
    await _login(client)
    _pin_test_offers(monkeypatch)
    await _seed_loyalty(chain_db, (MAIN, STORE, 150_000))

    plan_id = await _export(client, ASSEMBLY)
    response = await client.get(f"/plans/{plan_id}")
    assert response.status_code == 200
    assert "BPCs — LP front" in response.text
    assert "LP acquisition" in response.text
    assert "short 50,000 LP" in response.text


@respx.mock
async def test_roster_eligibility_line(client, chain_db):  # noqa: F811
    """The roster card's eligibility line and participation block: 'no
    active plans' until one is active, then per-PARTICIPANT counts of
    the active-plan nodes whose skill gates the character holds (the
    Typhoon chain: Industry 1 + the 22242 gates — the main 3/4, the
    corp-mate 2/4) plus the plan as a linked row with the target's
    commodity icon. The out-of-corp character was never pinned into
    the pool, so their card reads the not-in-a-pool line — skills
    aside, they cannot be assigned to a plan they were not planned
    into."""
    await _login(client)
    _mock_roster_esi()

    response = await client.get("/characters")
    assert response.status_code == 200
    # The label/value split: muted label span, white value span.
    assert '<span class="meta-label">Plan-eligible:</span>' in response.text
    assert '<span class="meta-value">— no active plans</span>' in response.text

    plan_id = await _export(client, TYPHOON)
    await client.post(f"/plans/{plan_id}/activate", follow_redirects=False)
    response = await client.get("/characters")
    assert response.status_code == 200
    assert "holds the skill gates for 3 of 4 active-plan nodes" in response.text
    assert "holds the skill gates for 2 of 4 active-plan nodes" in response.text
    assert (
        '<span class="meta-value">— not in an active plan\'s pool</span>'
        in response.text
    )
    # The participation block: the plan links to its detail page with
    # the target's commodity icon beside the name — participants only.
    assert f'href="/plans/{plan_id}"' in response.text
    assert "Typhoon ×10" in response.text
    assert "types/644/icon" in response.text
