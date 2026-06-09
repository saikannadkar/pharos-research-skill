# Pharos Research Skill

> A reusable MCP Skill that gives AI agents live research and structured intelligence capabilities — built for the [Pharos](https://pharos.network) RealFi ecosystem.

Submitted to: **Skill-to-Agent Dual Cascade Hackathon** (Phase 1) — DoraHacks

---

## What it does

AI agents making decisions in DeFi and RWA markets need reliable, up-to-date information *before* they act. This Skill is that research layer.

It exposes **3 MCP tools** any agent can call:

| Tool | What it does |
|---|---|
| `search_and_summarize` | Live web search → structured markdown summary (with focus modes) |
| `extract_structured_data` | Unstructured text → clean JSON fields |
| `compare_assets` | Two assets/protocols → comparison table + analysis |

### Example use case in a Pharos agent

```
Agent wants to invest in an RWA token on Pharos →
  1. calls search_and_summarize("TokenX RWA project", focus="risk")
  2. calls extract_structured_data(article_text, "audit_status, tvl, issuer")
  3. calls compare_assets("TokenX", "TokenY", criteria="yield, liquidity, risk")
  → Agent now has structured intelligence to make an informed onchain decision
```

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/<your-username>/pharos-research-skill
cd pharos-research-skill
pip install -r requirements.txt
```

**2. Set your API keys**
```bash
cp .env.example .env
# edit .env and fill in GROQ_API_KEY and TAVILY_API_KEY
```

Get keys (both free):
- Groq: https://console.groq.com
- Tavily: https://app.tavily.com

**3. Run the smoke tests**
```bash
python tests/test_tools.py
```

**4. Start the MCP server**
```bash
python skill/server.py
```

---

## MCP Configuration

Add to your MCP client (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "pharos-research-skill": {
      "command": "python",
      "args": ["/absolute/path/to/pharos-research-skill/skill/server.py"],
      "env": {
        "GROQ_API_KEY": "your_key",
        "TAVILY_API_KEY": "your_key"
      }
    }
  }
}
```

---

## Stack

- **MCP framework:** `mcp[cli]` (FastMCP)
- **LLM:** Groq — Llama 3 70B (free tier)
- **Search:** Tavily (free tier, agent-optimized)
- **Language:** Python 3.10+

---

## Project structure

```
pharos-research-skill/
├── SKILL.md              ← Skill descriptor (metadata + usage)
├── README.md
├── requirements.txt
├── .env.example
├── skill/
│   └── server.py         ← MCP server with all 3 tools
└── tests/
    └── test_tools.py     ← Smoke tests (no MCP client needed)
```
