"""
Pharos Research Skill — MCP Server
Exposes 3 tools for AI agents:
  1. search_and_summarize   — live web search + LLM summary
  2. extract_structured_data — pull key fields from raw text
  3. compare_assets          — structured side-by-side comparison
"""

import os
import json
from mcp.server.fastmcp import FastMCP
from groq import Groq
from tavily import TavilyClient

# ── clients ──────────────────────────────────────────────────────────────────
groq   = Groq(api_key=os.environ["GROQ_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

MODEL = "llama3-70b-8192"

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
    return resp.choices[0].message.content.strip()


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


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
