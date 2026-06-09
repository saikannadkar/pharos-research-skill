"""
Quick smoke tests for core tool behavior.
Does NOT require an MCP client. Just: python tests/test_tools.py
"""

import os
import sys
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("GROQ_API_KEY", "mock-test-key-not-for-production")
os.environ.setdefault("TAVILY_API_KEY", "mock-test-key-not-for-production")

# import the functions directly (not via MCP)
from skill.server import search_and_summarize, extract_structured_data, compare_assets, get_pharos_wallet_summary


def test_search_and_summarize():
    print("\n── Tool 1: search_and_summarize ─────────────────────────")
    with patch("skill.server._search", return_value=[{
        "title": "Pharos Network Overview",
        "url": "https://example.com/pharos",
        "content": "Pharos is an EVM-compatible Layer 1 focused on real-world assets."
    }]) as search_mock, patch(
        "skill.server._llm",
        return_value=(
            "## Summary\n\nPharos focuses on RWAs and throughput improvements.\n\n"
            "## Sources\n- https://example.com/pharos"
        ),
    ) as llm_mock:
        result = search_and_summarize(
            query="Pharos Network blockchain RWA",
            focus="financial"
        )
    print(result[:600])
    assert "sources" in result.lower(), "Expected sources section in summary"
    search_mock.assert_called_once_with("Pharos Network blockchain RWA")
    llm_mock.assert_called_once()
    print("✓ PASS")


def test_extract_structured_data():
    print("\n── Tool 2: extract_structured_data ──────────────────────")
    sample_text = """
    Pharos is a high-performance EVM-compatible Layer 1 blockchain focused on
    real-world assets. It raised $8M in seed funding and is backed by Ant Group
    alumni. The network targets 100,000 TPS and is expected to launch mainnet
    in 2026. Official site: pharos.network. Risk level: medium.
    """
    with patch(
        "skill.server._llm",
        return_value=(
            '{"project_name":"Pharos","funding_raised":"$8M","tps":"100,000",'
            '"mainnet_launch":"2026","risk_level":"medium","website":"pharos.network"}'
        ),
    ):
        result = extract_structured_data(
            text=sample_text,
            fields="project_name, funding_raised, tps, mainnet_launch, risk_level, website"
        )
    print(result)
    assert "pharos" in result.lower(), "Expected project name in output"
    print("✓ PASS")


def test_compare_assets():
    print("\n── Tool 3: compare_assets ───────────────────────────────")
    with patch(
        "skill.server._search",
        side_effect=[
            [{"title": "Bitcoin Overview", "content": "Strong security and decentralization."}],
            [{"title": "Ethereum Overview", "content": "Strong DeFi ecosystem and programmability."}],
        ],
    ) as search_mock, patch(
        "skill.server._llm",
        return_value=(
            "| Criteria | Bitcoin | Ethereum |\n|---|---|---|\n"
            "| Security | High | High |\n| Scalability | Lower | Higher |\n\n"
            "Bitcoin is conservative and secure, while Ethereum supports broader DeFi use cases."
        ),
    ) as llm_mock:
        result = compare_assets(
            asset_a="Bitcoin",
            asset_b="Ethereum",
            criteria="security, scalability, DeFi ecosystem, RWA support"
        )
    print(result[:600])
    assert "| Criteria | Bitcoin | Ethereum |" in result
    assert "bitcoin" in result.lower() and "ethereum" in result.lower()
    assert search_mock.call_count == 2
    llm_mock.assert_called_once()
    print("✓ PASS")
    
def test_get_pharos_wallet_summary():
    print("\n── Tool 4: get_pharos_wallet_summary ────────────────────")
    class MockResponse:
        def __init__(self, result):
            self._result = result

        def raise_for_status(self):
            pass

        def json(self):
            return {"result": self._result}

    def fake_post(url, **kwargs):
        assert url == "https://atlantic.dplabs-internal.com"
        payload = kwargs["json"]
        if payload["method"] == "eth_getBalance":
            return MockResponse("0xde0b6b3a7640000")  # 1 ETH-equivalent
        if payload["method"] == "eth_getTransactionCount":
            return MockResponse("0x2")
        return MockResponse("0x0")

    with patch("skill.server.requests.post", side_effect=fake_post):
        result = get_pharos_wallet_summary("0x0000000000000000000000000000000000000000")
    print(result)
    assert "PHRS" in result
    assert "**Transaction Count:** 2" in result
    print("✓ PASS")


if __name__ == "__main__":
    test_search_and_summarize()
    test_extract_structured_data()
    test_compare_assets()
    test_get_pharos_wallet_summary()

    print("\n✓ All tools passed.")
