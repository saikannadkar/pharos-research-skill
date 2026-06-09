# Pharos Research Skill — Technical Documentation

**Version:** 1.0.0  
**Author:** Sai Kannadkar  
**Hackathon:** Skill-to-Agent Dual Cascade — Phase 1 (DoraHacks / Pharos)  
**Protocol:** Model Context Protocol (MCP)  
**Language:** Python 3.10+

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Dependencies](#dependencies)
5. [Configuration](#configuration)
6. [Tools Reference](#tools-reference)
7. [Internal Helpers](#internal-helpers)
8. [Setup & Running](#setup--running)
9. [MCP Client Integration](#mcp-client-integration)
10. [Design Decisions](#design-decisions)
11. [Limitations](#limitations)

---

## Overview

Pharos Research Skill is a reusable MCP Skill — a standardized module that AI agents can call to complete specific tasks. It provides **live research and intelligence capabilities** for agents operating in DeFi, RWA (Real World Assets), and RealFi contexts, particularly on the Pharos blockchain network.

The core problem it solves: AI agents making onchain decisions need reliable, structured, up-to-date information *before* they act. This skill is the research layer — it fetches live data, processes it through an LLM, and returns clean structured output that downstream agent logic can act on directly.

**What it is NOT:** a full autonomous agent. It is a tool — a single capability module that an agent orchestrator calls as one step in a larger pipeline.

---

## Architecture

```
AI Agent (orchestrator)
    │
    │  JSON-RPC call (MCP protocol)
    ▼
MCP Server (skill/server.py)
    │
    ├── Tool 1: search_and_summarize
    │       ├── Tavily API  (live web search)
    │       └── Groq API    (LLM summarization)
    │
    ├── Tool 2: extract_structured_data
    │       └── Groq API    (LLM field extraction → JSON)
    │
    ├── Tool 3: compare_assets
    │       ├── Tavily API  (search both assets)
    │       └── Groq API    (LLM comparison table)
    │
    └── Tool 4: get_pharos_wallet_summary
            └── Pharos Atlantic Testnet RPC  (direct onchain read)
```

**MCP (Model Context Protocol)** is an open standard by Anthropic that defines how AI agents communicate with external tools. The agent sends a JSON-RPC call with a tool name and arguments; the MCP server executes the logic and returns a result. This server uses `FastMCP`, the high-level Python framework that handles all protocol-level concerns automatically.

**Pharos** is a high-performance EVM-compatible Layer 1 blockchain focused on Real World Assets (RWAs). It achieves up to 30,000 TPS with 1-second finality and is built by former AntChain/Alibaba engineers. This skill connects to the Pharos Atlantic Testnet for live onchain data.

---

## Project Structure

```
pharos-research-skill/
│
├── skill/
│   └── server.py          # MCP server — all 4 tools live here
│
├── tests/
│   └── test_tools.py      # Smoke tests (no MCP client needed)
│
├── SKILL.md               # Standard skill descriptor (metadata + usage)
├── DOCUMENTATION.md       # This file
├── README.md              # GitHub landing page
├── requirements.txt       # Python dependencies
├── .env.example           # Template for required environment variables
└── .gitignore             # Excludes .env and .venv from git
```

### Why this structure

`skill/server.py` is the only runtime file. Everything else is documentation or tooling. Keeping the server in a `skill/` subdirectory follows the standard Anthropic Agent Skills convention — agents and skill registries expect a `SKILL.md` at the root and the server code in a named subdirectory.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `mcp[cli]` | ≥1.0.0 | MCP server framework (FastMCP) |
| `groq` | ≥0.9.0 | Groq API client for Llama 3.3 70B |
| `tavily-python` | ≥0.3.0 | Tavily search API client |
| `python-dotenv` | ≥1.0.0 | Load `.env` file into environment |
| `requests` | (transitive) | HTTP calls to Pharos RPC |

**LLM:** Groq — Llama 3.3 70B Versatile (`llama-3.3-70b-versatile`). Chosen because it's free tier, fast (low latency inference), and the 70B size is sufficient for summarization and extraction tasks.

**Search:** Tavily — built specifically for AI agents. Returns cleaner, more relevant results than general search APIs for agent use cases. Free tier provides 1,000 searches/month.

**Onchain RPC:** Pharos Atlantic Testnet public endpoint. No API key required — it's a public JSON-RPC endpoint.

---

## Configuration

The server requires two environment variables. Set them in a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Get them here (both free, no credit card):
- Groq: https://console.groq.com → API Keys → Create
- Tavily: https://app.tavily.com → sign up → copy key

**Pharos RPC constants** (hardcoded in `server.py`, no key needed):

```python
PHAROS_RPC      = "https://atlantic.dplabs-internal.com"
PHAROS_CHAIN_ID = 688689
PHAROS_EXPLORER = "https://atlantic.pharosscan.xyz"
```

---

## Tools Reference

### Tool 1 — `search_and_summarize`

Search the live web for any query and return a structured markdown summary shaped by a focus mode.

**Signature:**
```python
def search_and_summarize(query: str, focus: str = "general") -> str
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | The search query. Be specific for best results. |
| `focus` | string | no | `"general"` | One of `general`, `financial`, `technical`, `risk` |

**Focus modes:**

| Mode | What the summary emphasises |
|---|---|
| `general` | Balanced overview of the topic |
| `financial` | Price, market cap, revenue, financial risks, metrics |
| `technical` | Architecture, protocols, tech stack, specs |
| `risk` | Red flags, regulatory concerns, downsides, vulnerabilities |

**How it works:**
1. Calls Tavily with the query, fetches top 5 results
2. Formats titles, URLs, and content snippets into a prompt
3. Sends to Groq LLM with a system prompt shaped by the focus mode
4. Returns a markdown-formatted summary with headers and a Sources section

**Example call:**
```json
{
  "tool": "search_and_summarize",
  "query": "Pharos Network RWA tokenization",
  "focus": "financial"
}
```

**Example output:**
```markdown
## Pharos Network — Financial Overview

**Funding:** $8M seed round
**Team:** Former AntChain, Alibaba blockchain engineers
**Performance:** 30,000 TPS, 1-second finality

### Key Financial Metrics
...

### Sources
1. https://pharosnetwork.xyz/...
2. https://messari.io/...
```

---

### Tool 2 — `extract_structured_data`

Extract specific named fields from any unstructured text and return clean JSON.

**Signature:**
```python
def extract_structured_data(text: str, fields: str) -> str
```

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | Raw unstructured text (article, report, whitepaper, etc.) Max 3,000 chars used. |
| `fields` | string | yes | Comma-separated list of field names to extract |

**How it works:**
1. Parses `fields` string into a list
2. Sends text + field list to Groq with strict instructions to return JSON only
3. Validates the response is parseable JSON (handles LLM backtick wrapping)
4. Returns pretty-printed JSON; missing fields are `null`

**JSON validation logic:** The LLM occasionally wraps output in markdown code fences (` ```json `). The tool strips these and retries parsing before returning an error object.

**Example call:**
```json
{
  "tool": "extract_structured_data",
  "text": "Pharos is an EVM-compatible L1 blockchain. It raised $8M in seed funding...",
  "fields": "project_name, funding_raised, chain_type, tps, risk_level"
}
```

**Example output:**
```json
{
  "project_name": "Pharos",
  "funding_raised": "$8M",
  "chain_type": "EVM-compatible L1",
  "tps": "30000",
  "risk_level": null
}
```

---

### Tool 3 — `compare_assets`

Research two assets or protocols independently and produce a structured comparison table plus written analysis.

**Signature:**
```python
def compare_assets(asset_a: str, asset_b: str, criteria: str = "") -> str
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `asset_a` | string | yes | — | First asset/protocol name |
| `asset_b` | string | yes | — | Second asset/protocol name |
| `criteria` | string | no | `"technology, use case, risk level, adoption, liquidity"` | Comma-separated comparison dimensions |

**How it works:**
1. Runs two Tavily searches: `"{asset_a} overview analysis 2025"` and `"{asset_b} overview analysis 2025"` (3 results each)
2. Formats both result sets into a single prompt
3. Sends to Groq with instructions to produce: (a) a markdown comparison table with criteria as rows, (b) a 3–5 sentence written analysis
4. Returns the combined output

**Example call:**
```json
{
  "tool": "compare_assets",
  "asset_a": "Pharos Network",
  "asset_b": "Ethereum",
  "criteria": "throughput, EVM compatibility, RWA support, ecosystem maturity"
}
```

**Example output:**
```markdown
| Criteria | Pharos Network | Ethereum |
|---|---|---|
| Throughput | 30,000 TPS | ~15-30 TPS (L1) |
| EVM Compatibility | Full | Native |
| RWA Support | Native, purpose-built | Via third-party protocols |
| Ecosystem Maturity | Early testnet | Mature, 8+ years |

**Analysis:** Pharos is purpose-built for institutional RWA use cases...
```

---

### Tool 4 — `get_pharos_wallet_summary`

Fetch live onchain data for any wallet address directly from the Pharos Atlantic Testnet via JSON-RPC.

**Signature:**
```python
def get_pharos_wallet_summary(address: str) -> str
```

**Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `address` | string | yes | A valid EVM wallet address (0x + 40 hex chars) |

**How it works:**
1. Validates address format (starts with `0x`, exactly 42 characters)
2. Makes two JSON-RPC calls to the Pharos Atlantic Testnet:
   - `eth_getBalance` — returns native PHRS balance in wei (hex)
   - `eth_getTransactionCount` — returns number of transactions sent from address (hex)
3. Converts hex wei to PHRS (divides by 10^18)
4. Returns formatted markdown summary with explorer link
5. Handles RPC timeout and error responses gracefully

**RPC calls made:**
```json
{"jsonrpc": "2.0", "method": "eth_getBalance", "params": ["0x...", "latest"], "id": 1}
{"jsonrpc": "2.0", "method": "eth_getTransactionCount", "params": ["0x...", "latest"], "id": 1}
```

**Example call:**
```json
{
  "tool": "get_pharos_wallet_summary",
  "address": "0xYourWalletAddressHere"
}
```

**Example output:**
```markdown
## Pharos Wallet Summary

**Address:** `0xYourWalletAddressHere`
**Balance:** 10.500000 PHRS
**Transaction Count:** 3
**Network:** Pharos Atlantic Testnet (Chain ID: 688689)
**Explorer:** https://atlantic.pharosscan.xyz/address/0xYourWalletAddressHere
```

**Error cases handled:**
- Invalid address format → returns descriptive error message
- RPC timeout (10s) → returns human-readable timeout message
- RPC error response → returns the error message from the node

---

## Internal Helpers

These functions are not exposed as MCP tools. They are private utilities used by the tools above.

### `_llm(system, user) → str`

Wraps a Groq chat completion call.

```python
def _llm(system: str, user: str) -> str
```

- Uses `llama-3.3-70b-versatile` model
- Temperature set to `0.2` — low randomness for consistent, factual outputs
- Returns the assistant message content as a plain string

### `_search(query, max_results) → list[dict]`

Wraps a Tavily search call.

```python
def _search(query: str, max_results: int = 5) -> list[dict]
```

- Returns a list of result dicts, each with `title`, `url`, `content`
- Returns empty list if no results found

---

## Setup & Running

**Prerequisites:** Python 3.10+, pip

```bash
# 1. Clone the repo
git clone https://github.com/your-username/pharos-research-skill
cd pharos-research-skill

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and TAVILY_API_KEY

# 5. Run smoke tests (verifies all tools work)
python tests/test_tools.py

# 6. Start the MCP server
python skill/server.py
```

The server stays running — this is correct. It listens for incoming tool calls from MCP clients. You will see no output until a client connects and calls a tool.

---

## MCP Client Integration

To use this skill from an MCP-compatible client (e.g. Claude Desktop), add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pharos-research-skill": {
      "command": "python",
      "args": ["C:/absolute/path/to/pharos-research-skill/skill/server.py"],
      "env": {
        "GROQ_API_KEY": "your_groq_key",
        "TAVILY_API_KEY": "your_tavily_key"
      }
    }
  }
}
```

Use the absolute path to `server.py`. On Windows use forward slashes or escaped backslashes.

---

## Design Decisions

**Why FastMCP over raw MCP SDK?**
FastMCP handles transport setup, tool registration, and JSON-RPC serialization automatically. The raw SDK requires significantly more boilerplate for the same result. For a skill (not a complex server), FastMCP is the right abstraction level.

**Why Groq over OpenAI?**
Free tier with no credit card required. The `llama-3.3-70b-versatile` model is capable enough for summarization and extraction. For a hackathon skill meant to be usable by anyone, zero-cost access matters.

**Why Tavily over SerpAPI or Google Search?**
Tavily is designed specifically for AI agent use — it returns cleaner content snippets, handles JavaScript-rendered pages better, and has a free tier suited for agent workloads. SerpAPI's free tier is more limited.

**Why temperature=0.2 for the LLM?**
These are research and extraction tasks, not creative ones. Lower temperature means more consistent, deterministic outputs — important when an agent is parsing the result programmatically.

**Why sequential searches in `compare_assets`?**
Parallel requests would require `asyncio` or threading, adding complexity. For a Phase 1 skill demo, sequential is correct — it keeps the code readable and the added latency (~2-3s) is acceptable.

**Why validate JSON in `extract_structured_data`?**
LLMs reliably produce JSON when instructed but occasionally wrap it in markdown code fences. The two-pass validation (parse → strip fences → parse again) handles the common failure case without over-engineering.

---

## Limitations

- **No caching** — every tool call makes fresh API requests. Repeated identical queries consume API quota.
- **Tavily free tier** — 1,000 searches/month. `compare_assets` uses 2 searches per call, `search_and_summarize` uses 1.
- **Pharos testnet only** — `get_pharos_wallet_summary` connects to the Atlantic Testnet, not mainnet (mainnet not yet live as of June 2026).
- **Text truncation** — `extract_structured_data` truncates input to 3,000 characters. Longer documents need chunking before passing to this tool.
- **Sequential search** — `compare_assets` makes two searches sequentially (~4-6s total). Could be parallelized with `asyncio` in a production version.
- **No auth** — the MCP server has no authentication layer. Anyone with access to the running process can call the tools.