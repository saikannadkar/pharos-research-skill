"""
Pharos Research Skill — MCP Server
Exposes 3 tools for AI agents:
  1. search_and_summarize   — live web search + LLM summary
  2. extract_structured_data — pull key fields from raw text
  3. compare_assets          — structured side-by-side comparison
"""

import os
import json
import requests
from mcp.server.fastmcp import FastMCP
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ── Pharos testnet config ─────────────────────────────────────────────────────
PHAROS_RPC      = "https://atlantic.dplabs-internal.com"
PHAROS_CHAIN_ID = 688689
PHAROS_EXPLORER = "https://atlantic.pharosscan.xyz"
# ── clients ──────────────────────────────────────────────────────────────────
groq   = Groq(api_key=os.environ["GROQ_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

MODEL = "llama-3.3-70b-versatile"

mcp = FastMCP("pharos-research-skill")


# ── helpers ───────────────────────────────────────────────────────────────────
def _llm(system: str, user: str) -> str:
    resp = groq.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    return content.strip() if content else ""


def _search(query: str, max_results: int = 5) -> list[dict]:
    results = tavily.search(query=query, max_results=max_results)
    return results.get("results", [])


# ── tool 1 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def search_and_summarize(query: str, focus: str = "general") -> str:
    """
    Search the web for a query and return a structured summary.

    Args:
        query:  What to search for. Be specific.
        focus:  One of 'general' | 'financial' | 'technical' | 'risk'.
                Shapes what the summary emphasises.

    Returns:
        A structured markdown summary with key findings and sources.
    """
    results = _search(query)
    if not results:
        return "No results found for the given query."

    snippets = "\n\n".join(
        f"[{i+1}] {r['title']}\nURL: {r['url']}\n{r.get('content', '')[:400]}"
        for i, r in enumerate(results)
    )

    focus_instruction = {
        "general":   "Provide a balanced overview.",
        "financial": "Focus on price, market cap, revenue, risks, and financial metrics.",
        "technical": "Focus on technology, architecture, protocols, and technical specs.",
        "risk":      "Focus on risks, red flags, regulatory concerns, and downsides.",
    }.get(focus, "Provide a balanced overview.")

    summary = _llm(
        system=(
            "You are a research analyst for an AI agent. "
            "Given web search results, produce a concise structured summary. "
            f"{focus_instruction} "
            "Format: use markdown with headers. End with a 'Sources' list."
        ),
        user=f"Query: {query}\n\nSearch Results:\n{snippets}",
    )

    return summary


# ── tool 2 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def extract_structured_data(text: str, fields: str) -> str:
    """
    Extract specific fields from unstructured text and return JSON.

    Args:
        text:   Raw text to extract from (article, report, description, etc.)
        fields: Comma-separated list of fields to extract.
                e.g. "token_name, price, market_cap, risk_level, website"

    Returns:
        A JSON string with extracted fields. Missing fields are null.
    """
    field_list = [f.strip() for f in fields.split(",")]

    result = _llm(
        system=(
            "You are a data extraction engine. "
            "Extract the requested fields from the provided text. "
            "Return ONLY a valid JSON object — no explanation, no markdown. "
            "If a field cannot be found, set its value to null."
        ),
        user=(
            f"Fields to extract: {json.dumps(field_list)}\n\n"
            f"Text:\n{text[:3000]}"
        ),
    )

    # validate it's actually JSON before returning
    try:
        parsed = json.loads(result)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        # LLM sometimes wraps in backticks — strip and retry
        cleaned = result.strip().strip("```json").strip("```").strip()
        try:
            parsed = json.loads(cleaned)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "Could not parse extracted data", "raw": result})


# ── tool 3 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def compare_assets(asset_a: str, asset_b: str, criteria: str = "") -> str:
    """
    Research and compare two assets, protocols, or projects side by side.

    Args:
        asset_a:  First asset/project name (e.g. "Ethereum", "Uniswap", "Gold")
        asset_b:  Second asset/project name
        criteria: Optional comma-separated comparison dimensions.
                  e.g. "security, yield, liquidity, regulation"
                  Defaults to a standard financial/technical comparison.

    Returns:
        A structured markdown comparison table + written analysis.
    """
    # search both in parallel (sequential here, fine for hackathon)
    results_a = _search(f"{asset_a} overview analysis 2025", max_results=3)
    results_b = _search(f"{asset_b} overview analysis 2025", max_results=3)

    def _snippets(results):
        return "\n".join(
            f"- {r['title']}: {r.get('content', '')[:250]}"
            for r in results
        )

    criteria_str = (
        criteria if criteria
        else "technology, use case, risk level, adoption, liquidity"
    )

    comparison = _llm(
        system=(
            "You are a financial and technical research analyst. "
            "Compare two assets or projects based on provided research. "
            "Format your response as: "
            "1) A markdown comparison table with the given criteria as rows. "
            "2) A short written analysis (3-5 sentences) on which suits what use case. "
            "Be factual and concise."
        ),
        user=(
            f"Compare: {asset_a} vs {asset_b}\n"
            f"Criteria: {criteria_str}\n\n"
            f"Research on {asset_a}:\n{_snippets(results_a)}\n\n"
            f"Research on {asset_b}:\n{_snippets(results_b)}"
        ),
    )

    return comparison


# ── tool 4 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def get_pharos_wallet_summary(address: str) -> str:
    """
    Fetch live onchain data for a wallet address on the Pharos testnet.
    Returns native PHRS balance and current transaction count.

    Args:
        address: A valid EVM wallet address (0x...)

    Returns:
        A summary string with balance, tx count, and explorer link.
    """
    if not address.startswith("0x") or len(address) != 42:
        return "Invalid address. Must be a 42-character hex string starting with 0x."

    def _rpc(method: str, params: list):
        resp = requests.post(
            PHAROS_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"]["message"])
        return data["result"]

    try:
        balance_hex  = _rpc("eth_getBalance",      [address, "latest"])
        tx_count_hex = _rpc("eth_getTransactionCount", [address, "latest"])
    except requests.exceptions.Timeout:
        return "Pharos RPC timed out. The testnet may be temporarily slow."
    except Exception as e:
        return f"RPC error: {str(e)}"

    # convert hex wei → PHRS (18 decimals)
    balance_wei  = int(balance_hex, 16)
    balance_phrs = balance_wei / 10**18
    tx_count     = int(tx_count_hex, 16)

    return (
        f"## Pharos Wallet Summary\n\n"
        f"**Address:** `{address}`\n"
        f"**Balance:** {balance_phrs:.6f} PHRS\n"
        f"**Transaction Count:** {tx_count}\n"
        f"**Network:** Pharos Testnet (Chain ID: {PHAROS_CHAIN_ID})\n"
        f"**Explorer:** {PHAROS_EXPLORER}/address/{address}\n"
    )

# ── tool 5 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def get_pharos_network_stats() -> str:
    """
    Fetch live network statistics from the Pharos Atlantic Testnet.
    Returns current block number, gas price, and chain info.

    Returns:
        A markdown summary of current Pharos network health.
    """
    def _rpc(method: str, params: list):
        resp = requests.post(
            PHAROS_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"]["message"])
        return data["result"]

    try:
        block_hex    = _rpc("eth_blockNumber", [])
        gas_hex      = _rpc("eth_gasPrice", [])
        chain_hex    = _rpc("eth_chainId", [])
    except requests.exceptions.Timeout:
        return "Pharos RPC timed out. The testnet may be temporarily slow."
    except Exception as e:
        return f"RPC error: {str(e)}"

    block_number = int(block_hex, 16)
    gas_gwei     = int(gas_hex, 16) / 10**9
    chain_id     = int(chain_hex, 16)

    return (
        f"## Pharos Network Stats\n\n"
        f"**Network:** Pharos Atlantic Testnet\n"
        f"**Chain ID:** {chain_id}\n"
        f"**Latest Block:** {block_number:,}\n"
        f"**Gas Price:** {gas_gwei:.4f} Gwei\n"
        f"**Explorer:** {PHAROS_EXPLORER}\n"
        f"**RPC:** {PHAROS_RPC}\n"
    )


# ── tool 6 ────────────────────────────────────────────────────────────────────
@mcp.tool()
def get_pharos_recent_transactions(address: str, limit: int = 5) -> str:
    """
    Fetch recent transactions for a wallet address on the Pharos Atlantic Testnet.
    Scans the last 1000 blocks for transactions involving this address.

    Args:
        address: A valid EVM wallet address (0x...)
        limit:   Max number of transactions to return (default 5, max 10)

    Returns:
        A markdown list of recent transactions with hash, block, and value.
    """
    if not address.startswith("0x") or len(address) != 42:
        return "Invalid address. Must be a 42-character hex string starting with 0x."

    limit = min(limit, 10)

    def _rpc(method: str, params: list):
        resp = requests.post(
            PHAROS_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise ValueError(data["error"]["message"])
        return data["result"]

    try:
        latest_hex   = _rpc("eth_blockNumber", [])
        latest_block = int(latest_hex, 16)
        from_block   = hex(max(0, latest_block - 1000))

        # fetch logs where address is sender or receiver
        logs = _rpc("eth_getLogs", [{
            "fromBlock": from_block,
            "toBlock":   "latest",
            "address":   None,
            "topics":    []
        }])

        # fetch last N blocks and scan for txs involving this address
        txs = []
        scan_from = max(0, latest_block - 50)

        for block_num in range(latest_block, scan_from, -1):
            if len(txs) >= limit:
                break
            block = _rpc("eth_getBlockByNumber", [hex(block_num), True])
            if not block or not block.get("transactions"):
                continue
            for tx in block["transactions"]:
                if (
                    tx.get("from", "").lower() == address.lower()
                    or tx.get("to", "").lower() == address.lower()
                ):
                    txs.append(tx)
                    if len(txs) >= limit:
                        break

    except requests.exceptions.Timeout:
        return "Pharos RPC timed out. The testnet may be temporarily slow."
    except Exception as e:
        return f"RPC error: {str(e)}"

    if not txs:
        return (
            f"No recent transactions found for `{address}` "
            f"in the last 50 blocks.\n\n"
            f"View full history: {PHAROS_EXPLORER}/address/{address}"
        )

    lines = [f"## Recent Transactions for `{address}`\n"]
    for tx in txs:
        value_phrs = int(tx.get("value", "0x0"), 16) / 10**18
        direction  = "OUT" if tx.get("from", "").lower() == address.lower() else "IN"
        block_num  = int(tx.get("blockNumber", "0x0"), 16)
        tx_hash    = tx.get("hash", "N/A")
        to_addr    = tx.get("to") or "Contract Deploy"

        lines.append(
            f"- **{direction}** | Block `{block_num:,}` | "
            f"`{value_phrs:.4f}` PHRS | "
            f"[{tx_hash[:16]}...]({PHAROS_EXPLORER}/tx/{tx_hash})"
        )

    lines.append(f"\n**Full history:** {PHAROS_EXPLORER}/address/{address}")
    return "\n".join(lines)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
