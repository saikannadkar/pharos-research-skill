# Contributing

Thanks for your interest in contributing to Pharos Research Skill.

## Getting started

```bash
git clone https://github.com/your-username/pharos-research-skill
cd pharos-research-skill
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# add your keys to .env
```

## Running tests

```bash
python tests/test_tools.py
```

All 4 tools must pass before submitting a PR.

## Adding a new tool

1. Add your function to `skill/server.py` with the `@mcp.tool()` decorator
2. Write a docstring with `Args:` and `Returns:` sections — MCP uses these
3. Add a test case in `tests/test_tools.py`
4. Document it in `DOCUMENTATION.md` under Tools Reference
5. Add a usage example in `SKILL.md`

## Guidelines

- One tool per PR — keep changes focused
- Match the existing code style
- No new dependencies without a good reason
- Don't commit `.env` or `.venv`
