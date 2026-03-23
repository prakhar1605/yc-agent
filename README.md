# 🚀 YC Startup Research Agent

Multi-agent AI system using **LangGraph** + **Streamlit** + **OpenRouter API**.

---

## 🏗️ Architecture

```
User Input
    ↓
[Searcher Agent] ──→ [Analyst Agent] ──→ [Critic Agent]
     ↑                                         │
     └─────── (Score < 7 → Loop back) ─────────┘
                                               │
                                    (Score ≥ 7 → Final Report)
```

**3 Agents:**
- 🔍 **Searcher** — DuckDuckGo web search, query refinement
- 📈 **Investment Analyst** — Funding analysis, business model evaluation
- 🎯 **Critic** — Quality scoring (1-10), self-correction loop

---

## ⚡ Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. API Key set karo
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# 3. Run!
streamlit run app.py
```

---

## 🌐 OpenRouter Setup

1. openrouter.ai pe account banao
2. API Keys section mein key generate karo
3. Free model: `meta-llama/llama-3.1-70b-instruct:free`
4. Cheap model: `anthropic/claude-3.5-haiku`

---

## 📁 Files

- `app.py` — Streamlit UI
- `agents.py` — LangGraph multi-agent logic
- `requirements.txt` — Dependencies
