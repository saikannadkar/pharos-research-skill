---
name: pharos-research-skill
version: 1.0.0
description: >
  A research and intelligence skill for AI agents. Enables live web search
  with structured summarization, field extraction from unstructured text,
  and side-by-side asset comparison. Designed for agents operating in
  DeFi, RWA, and RealFi contexts — particularly on the Pharos network.
author: Sai Kannadkar
tags: [research, summarization, extraction, comparison, defi, rwa, pharos]
mcp_compatible: true
---

# Pharos Research Skill

A reusable MCP Skill that gives any AI agent live research and structured
intelligence capabilities — purpose-built for the Pharos RealFi ecosystem.

## Why this Skill exists

AI agents making onchain decisions (DeFi swaps, RWA investments, protocol
interactions) need reliable, up-to-date information *before* they act.
This Skill is the research layer: it fetches live web data, structures it,
and returns clean output that downstream agent tools can act on.

## Tools

### `search_and_summarize`
Search the web for any query and get a structured markdown summary.
Supports focus modes: `general`, `financial`, `technical`, `risk`.

**Example agent call:**
```json
{
  "tool": "search_and_summarize",
  "query": "Pharos Network RWA tokenization 2025",
  "focus": "financial"
}
```

### `extract_structured_data`
Extract specific fields from raw unstructured text (articles, reports,
whitepapers) and return clean JSON.

**Example agent call:**
```json
{
  "tool": "extract_structured_data",
  "text": "<raw article or report text>",
  "fields": "protocol_name, tvl, audit_status, chain, risk_level"
}
```

### `compare_assets`
Research and compare two assets or protocols side by side. Returns a
markdown comparison table and a written analysis.

**Example agent call:**
```json
{
  "tool": "compare_assets",
  "asset_a": "Pharos Network",
  "asset_b": "Ethereum",
  "criteria": "throughput, EVM compatibility, RWA support, ecosystem maturity"
}
```

## Setup

```bash
git clone https://github.com/<your-username>/pharos-research-skill
cd pharos-research-skill
pip install -r requirements.txt

export GROQ_API_KEY=your_key_here
export TAVILY_API_KEY=your_key_here

python skill/server.py
```

## MCP Configuration

Add to your MCP client config (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pharos-research-skill": {
      "command": "python",
      "args": ["skill/server.py"],
      "env": {
        "GROQ_API_KEY": "your_key_here",
        "TAVILY_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Dependencies

- `mcp[cli]` — MCP server framework
- `groq` — LLM inference (Llama 3 70B)
- `tavily-python` — live web search
- `python-dotenv` — local env management
