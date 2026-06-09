from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(".env"))

import os
print("Keys loaded:", bool(os.getenv("GROQ_API_KEY")), bool(os.getenv("TAVILY_API_KEY")))

print("Testing Tavily...")
from tavily import TavilyClient
t = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
r = t.search(query="Pharos blockchain", max_results=2)
print("Tavily OK:", len(r.get("results", [])), "results")

print("Testing Groq...")
from groq import Groq
g = Groq(api_key=os.getenv("GROQ_API_KEY"))
resp = g.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello in one word."}],
    max_tokens=10,
)
print("Groq OK:", resp.choices[0].message.content)