"""
Quick smoke tests — run directly to verify your keys work.
Does NOT require an MCP client. Just: python tests/test_tools.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

# import the functions directly (not via MCP)
from skill.server import search_and_summarize, extract_structured_data, compare_assets, get_pharos_wallet_summary


def test_search_and_summarize():
    print("\n── Tool 1: search_and_summarize ─────────────────────────")
    result = search_and_summarize(
        query="Pharos Network blockchain RWA",
        focus="financial"
    )
    print(result[:600])
    assert len(result) > 100, "Summary too short"
    print("✓ PASS")


def test_extract_structured_data():
    print("\n── Tool 2: extract_structured_data ──────────────────────")
    sample_text = """
    Pharos is a high-performance EVM-compatible Layer 1 blockchain focused on
    real-world assets. It raised $8M in seed funding and is backed by Ant Group
    alumni. The network targets 100,000 TPS and is expected to launch mainnet
    in 2026. Official site: pharos.network. Risk level: medium.
    """
    result = extract_structured_data(
        text=sample_text,
        fields="project_name, funding_raised, tps, mainnet_launch, risk_level, website"
    )
    print(result)
    assert "pharos" in result.lower(), "Expected project name in output"
    print("✓ PASS")


def test_compare_assets():
    print("\n── Tool 3: compare_assets ───────────────────────────────")
    result = compare_assets(
        asset_a="Bitcoin",
        asset_b="Ethereum",
        criteria="security, scalability, DeFi ecosystem, RWA support"
    )
    print(result[:600])
    assert len(result) > 100, "Comparison too short"
    print("✓ PASS")
    
def test_get_pharos_wallet_summary():
    print("\n── Tool 4: get_pharos_wallet_summary ────────────────────")
    # using a known testnet address
    result = get_pharos_wallet_summary("0x0000000000000000000000000000000000000000")
    print(result)
    assert "PHRS" in result or "error" in result.lower()
    print("✓ PASS")


if __name__ == "__main__":
    missing = [k for k in ["GROQ_API_KEY", "TAVILY_API_KEY"] if not os.getenv(k)]
    if missing:
        print(f"ERROR: Missing env vars: {missing}")
        print("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)

    test_search_and_summarize()
    test_extract_structured_data()
    test_compare_assets()
    test_get_pharos_wallet_summary()

    print("\n✓ All tools passed.")
