import httpx
import pytest
import respx

from app.services.apewisdom_client import ApeWisdomClientError, fetch_stocks, _parse_payload


def test_parse_payload_coerces_strings():
    payload = {
        "results": [
            {
                "rank": "1",
                "ticker": "nvda",
                "mentions": "100",
                "upvotes": "50",
                "mentions_24h_ago": "80",
            }
        ]
    }
    rows = _parse_payload(payload, top_n=50)
    assert len(rows) == 1
    assert rows[0].ticker == "NVDA"
    assert rows[0].mentions == 100
    assert rows[0].mentions_24h_ago == 80


def test_parse_payload_skips_invalid_rows():
    payload = {
        "results": [
            {"rank": 1, "ticker": "OK", "mentions": 10, "upvotes": 1, "mentions_24h_ago": 5},
            {"rank": 2, "mentions": 10, "upvotes": 1},
        ]
    }
    rows = _parse_payload(payload, top_n=50)
    assert len(rows) == 1
    assert rows[0].ticker == "OK"


def test_parse_payload_empty_raises():
    with pytest.raises(ApeWisdomClientError):
        _parse_payload({"results": []}, top_n=50)


@respx.mock
@pytest.mark.asyncio
async def test_fetch_stocks_success():
    respx.get("https://apewisdom.io/api/v1.0/filter/all-stocks").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "rank": 1,
                        "ticker": "SPY",
                        "mentions": 136,
                        "upvotes": 100,
                        "mentions_24h_ago": 108,
                    }
                ]
            },
        )
    )
    rows = await fetch_stocks(top_n=50)
    assert rows[0].ticker == "SPY"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_stocks_retries_then_fails():
    route = respx.get("https://apewisdom.io/api/v1.0/filter/all-stocks").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(ApeWisdomClientError):
        await fetch_stocks(top_n=50)
    assert route.call_count == 3
