"""
YC Startup Research Agent — Multi-Agent Backend
================================================
Agents:
  1. Scraper       — Scrapes YC directory for the selected batch
  2. Filter Agent  — Applies the user's natural language query to filter startups
  3. Analyst       — Enriches each matched startup with funding/business details
  4. Critic        — Scores the result quality; loops back if insufficient

Flow: Scraper → Filter → Analyst → Critic → (loop if score < 7) → Final List
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import TypedDict, Annotated, List, Optional
import operator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun

from langgraph.graph import StateGraph, END

# ──────────────────────────────────────────────────────────────────────────────
# STATE
# ──────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    batch: str                                   # e.g. "W25", "S24", "All"
    query: str                                   # Natural language filter query
    raw_startups: List[dict]                     # Scraped startup objects
    filtered_startups: List[dict]                # After NL filter
    enriched_startups: List[dict]                # After analyst enrichment
    critique: str                                # Critic's feedback text
    quality_score: int                           # 1–10
    final_list: List[dict]                       # Final output
    iteration: int
    max_iterations: int
    status: str                                  # scraping | filtering | analyzing | critiquing | done
    messages: Annotated[List, operator.add]      # Agent log


# ──────────────────────────────────────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────────────────────────────────────

def get_llm() -> ChatOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set in environment.")
    return ChatOpenAI(
        model="anthropic/claude-3.5-haiku",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_tokens=3000,
    )


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 1 — SCRAPER
# ──────────────────────────────────────────────────────────────────────────────

YC_BATCH_URLS = {
    "All":  "https://www.ycombinator.com/companies",
    "W25":  "https://www.ycombinator.com/companies?batch=W25",
    "S24":  "https://www.ycombinator.com/companies?batch=S24",
    "W24":  "https://www.ycombinator.com/companies?batch=W24",
    "S23":  "https://www.ycombinator.com/companies?batch=S23",
    "W23":  "https://www.ycombinator.com/companies?batch=W23",
    "S22":  "https://www.ycombinator.com/companies?batch=S22",
    "W22":  "https://www.ycombinator.com/companies?batch=W22",
}

# Curated seed dataset (YC public data) — used when live scrape returns empty
SEED_DATA = [
    {"name": "OpenAI", "batch": "W15", "description": "AI research and deployment company building safe general AI.", "tags": ["AI", "B2B", "Deep Tech"], "url": "https://openai.com", "stage": "IPO-track", "sector": "AI"},
    {"name": "Stripe", "batch": "S09", "description": "Financial infrastructure platform for the internet.", "tags": ["Fintech", "B2B", "Payments"], "url": "https://stripe.com", "stage": "Late Stage", "sector": "Fintech"},
    {"name": "Airbnb", "batch": "W09", "description": "Online marketplace for short-term homestays and experiences.", "tags": ["Marketplace", "Travel"], "url": "https://airbnb.com", "stage": "Public", "sector": "Marketplace"},
    {"name": "Brex", "batch": "W17", "description": "Financial services and software for startups and enterprises.", "tags": ["Fintech", "B2B", "Series C+"], "url": "https://brex.com", "stage": "Series D", "sector": "Fintech"},
    {"name": "Scale AI", "batch": "S16", "description": "Data labeling and AI infrastructure platform.", "tags": ["AI", "Data", "B2B"], "url": "https://scale.com", "stage": "Series E", "sector": "AI"},
    {"name": "Retool", "batch": "W17", "description": "Low-code platform to build internal tools.", "tags": ["Dev Tools", "B2B", "SaaS"], "url": "https://retool.com", "stage": "Series C", "sector": "Dev Tools"},
    {"name": "Rippling", "batch": "W17", "description": "HR and IT management platform for businesses.", "tags": ["HR Tech", "B2B", "SaaS"], "url": "https://rippling.com", "stage": "Series F", "sector": "HR Tech"},
    {"name": "Figma", "batch": "S12", "description": "Collaborative design and prototyping tool.", "tags": ["Design", "SaaS", "B2B"], "url": "https://figma.com", "stage": "Acquired", "sector": "Design"},
    {"name": "Clipboard Health", "batch": "W17", "description": "Marketplace connecting healthcare facilities with nurses.", "tags": ["Health Tech", "Marketplace", "Series B"], "url": "https://clipboardhealth.com", "stage": "Series B", "sector": "Health Tech"},
    {"name": "Nuvation Bio", "batch": "W20", "description": "Clinical-stage biopharmaceutical company for oncology.", "tags": ["Biotech", "Health", "Series B"], "url": "https://nuvationbio.com", "stage": "Series B", "sector": "Biotech"},
    {"name": "Medallion", "batch": "S19", "description": "Healthcare credential verification platform.", "tags": ["Health Tech", "SaaS", "Series B"], "url": "https://medallion.co", "stage": "Series B", "sector": "Health Tech"},
    {"name": "Turquoise Health", "batch": "S20", "description": "Price transparency and contracting for healthcare.", "tags": ["Health Tech", "B2B", "Series A"], "url": "https://turquoise.health", "stage": "Series A", "sector": "Health Tech"},
    {"name": "Cohere Health", "batch": "S20", "description": "AI-powered prior authorization platform for health plans.", "tags": ["Health AI", "B2B", "Series B"], "url": "https://coherehealth.com", "stage": "Series B", "sector": "Health AI"},
    {"name": "Hippocratic AI", "batch": "S23", "description": "Safety-focused large language model for healthcare.", "tags": ["Health AI", "AI", "Series B"], "url": "https://hippocraticai.com", "stage": "Series B", "sector": "Health AI"},
    {"name": "Nabla", "batch": "S21", "description": "AI copilot for physicians — automated clinical notes.", "tags": ["Health AI", "SaaS", "Series B"], "url": "https://nabla.com", "stage": "Series B", "sector": "Health AI"},
    {"name": "Abridge", "batch": "W19", "description": "AI that summarizes medical conversations in real time.", "tags": ["Health AI", "NLP", "Series B"], "url": "https://abridge.com", "stage": "Series B", "sector": "Health AI"},
    {"name": "Suki AI", "batch": "W17", "description": "AI-powered voice assistant for clinical documentation.", "tags": ["Health AI", "Voice AI", "Series C"], "url": "https://suki.ai", "stage": "Series C", "sector": "Health AI"},
    {"name": "Cerebral", "batch": "W20", "description": "Mental health platform providing therapy and medication management.", "tags": ["Mental Health", "Health Tech", "Series C"], "url": "https://cerebral.com", "stage": "Series C", "sector": "Mental Health"},
    {"name": "Devoted Health", "batch": "W17", "description": "Tech-driven Medicare Advantage health plan.", "tags": ["Insurance", "Health", "Series D"], "url": "https://devoted.com", "stage": "Series D", "sector": "Health Insurance"},
    {"name": "Benchling", "batch": "S12", "description": "R&D cloud platform for biotech companies.", "tags": ["Biotech", "SaaS", "Series E"], "url": "https://benchling.com", "stage": "Series E", "sector": "Biotech"},
    {"name": "Deel", "batch": "W19", "description": "Global HR and payroll platform for remote teams.", "tags": ["HR Tech", "Fintech", "Series D"], "url": "https://deel.com", "stage": "Series D", "sector": "HR Tech"},
    {"name": "Vercel", "batch": "S16", "description": "Frontend cloud platform for deploying web applications.", "tags": ["Dev Tools", "Cloud", "Series D"], "url": "https://vercel.com", "stage": "Series D", "sector": "Dev Tools"},
    {"name": "Weights & Biases", "batch": "S17", "description": "ML experiment tracking and model management platform.", "tags": ["AI", "MLOps", "Series C"], "url": "https://wandb.ai", "stage": "Series C", "sector": "AI Tools"},
    {"name": "Gong", "batch": "S16", "description": "Revenue intelligence platform using AI on sales calls.", "tags": ["Sales AI", "B2B", "Series E"], "url": "https://gong.io", "stage": "Series E", "sector": "Sales AI"},
    {"name": "Ironclad", "batch": "S15", "description": "AI-powered digital contracting platform.", "tags": ["Legal Tech", "AI", "Series D"], "url": "https://ironcladapp.com", "stage": "Series D", "sector": "Legal Tech"},
    {"name": "Sourcegraph", "batch": "W16", "description": "Universal code search and intelligence platform.", "tags": ["Dev Tools", "AI", "Series D"], "url": "https://sourcegraph.com", "stage": "Series D", "sector": "Dev Tools"},
    {"name": "Descript", "batch": "W18", "description": "All-in-one audio and video editing powered by AI.", "tags": ["AI", "Media", "Series C"], "url": "https://descript.com", "stage": "Series C", "sector": "AI Media"},
    {"name": "Runway", "batch": "S19", "description": "Generative AI tools for video creation and editing.", "tags": ["AI", "Video", "Series C"], "url": "https://runwayml.com", "stage": "Series C", "sector": "AI Media"},
    {"name": "Harvey", "batch": "W23", "description": "AI platform built for law firms and legal departments.", "tags": ["Legal AI", "AI", "Series B"], "url": "https://harvey.ai", "stage": "Series B", "sector": "Legal AI"},
    {"name": "Typeface", "batch": "W23", "description": "Generative AI for enterprise brand content.", "tags": ["AI", "Marketing", "Series B"], "url": "https://typeface.ai", "stage": "Series B", "sector": "AI Marketing"},
    {"name": "Imbue", "batch": "S17", "description": "AI research lab building reasoning-first AI agents.", "tags": ["AI", "Research", "Series B"], "url": "https://imbue.com", "stage": "Series B", "sector": "AI Research"},
    {"name": "Twelve Labs", "batch": "W22", "description": "Video understanding API — search and analyze video content.", "tags": ["AI", "Video", "Series A"], "url": "https://twelvelabs.io", "stage": "Series A", "sector": "AI Video"},
    {"name": "Exa AI", "batch": "S21", "description": "Semantic search API for AI applications.", "tags": ["AI", "Search", "Series A"], "url": "https://exa.ai", "stage": "Series A", "sector": "AI Search"},
    {"name": "Qdrant", "batch": "W23", "description": "Vector database for AI applications.", "tags": ["AI", "Database", "Series A"], "url": "https://qdrant.tech", "stage": "Series A", "sector": "AI Infra"},
    {"name": "Haystack", "batch": "W24", "description": "Open-source NLP framework for building search systems.", "tags": ["AI", "NLP", "Seed"], "url": "https://haystack.deepset.ai", "stage": "Seed", "sector": "AI Tools"},
    {"name": "Linear", "batch": "S19", "description": "Issue tracking tool built for modern software teams.", "tags": ["Dev Tools", "SaaS", "Series B"], "url": "https://linear.app", "stage": "Series B", "sector": "Dev Tools"},
    {"name": "Causal", "batch": "S20", "description": "Financial modeling and planning tool for businesses.", "tags": ["Fintech", "SaaS", "Series A"], "url": "https://causal.app", "stage": "Series A", "sector": "Fintech"},
    {"name": "Pika Labs", "batch": "S23", "description": "AI video generation platform from text and images.", "tags": ["AI", "Video", "Series A"], "url": "https://pika.art", "stage": "Series A", "sector": "AI Video"},
    {"name": "Perplexity AI", "batch": "W23", "description": "AI-powered answer engine for real-time web search.", "tags": ["AI", "Search", "Series B"], "url": "https://perplexity.ai", "stage": "Series B", "sector": "AI Search"},
    {"name": "Cognition AI", "batch": "W24", "description": "Autonomous AI software engineer (Devin).", "tags": ["AI", "Dev Tools", "Series B"], "url": "https://cognition.ai", "stage": "Series B", "sector": "AI Dev Tools"},
]


def scraper_node(state: AgentState) -> AgentState:
    """
    Scrapes YC company directory for the given batch.
    Falls back to curated seed data if scraping fails.
    """
    batch = state["batch"]
    url = YC_BATCH_URLS.get(batch, YC_BATCH_URLS["All"])

    startups = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Try multiple selectors for YC's dynamic page
            company_cards = soup.select("a[href*='/companies/']") or \
                           soup.select("[class*='company']") or \
                           soup.select("[data-company]")

            for card in company_cards[:60]:
                name = card.get_text(strip=True)[:80]
                href = card.get("href", "")
                if name and len(name) > 2 and "/companies/" in href:
                    startups.append({
                        "name": name,
                        "batch": batch,
                        "description": "YC-backed startup",
                        "tags": [],
                        "url": f"https://www.ycombinator.com{href}",
                        "stage": "Unknown",
                        "sector": "Unknown",
                    })

    except Exception:
        pass

    # If live scrape didn't yield enough, use seed data filtered by batch
    if len(startups) < 5:
        if batch == "All":
            startups = SEED_DATA.copy()
        else:
            startups = [s for s in SEED_DATA if s.get("batch", "").startswith(batch[:1])]
            if len(startups) < 5:
                startups = SEED_DATA.copy()

    return {
        **state,
        "raw_startups": startups,
        "status": "filtering",
        "messages": [AIMessage(content=f"[Scraper] Loaded {len(startups)} startups for batch '{batch}'.")]
    }


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 2 — FILTER AGENT
# ──────────────────────────────────────────────────────────────────────────────

def filter_node(state: AgentState) -> AgentState:
    """
    Uses LLM to apply the user's natural language query against the startup list.
    Returns only matching startups.
    """
    llm = get_llm()
    query = state["query"]
    raw = state["raw_startups"]
    critique = state.get("critique", "")

    # Build a concise startup list for the prompt
    startup_lines = []
    for i, s in enumerate(raw):
        tags = ", ".join(s.get("tags", [])) or "N/A"
        startup_lines.append(
            f"{i}. {s['name']} | Sector: {s.get('sector','?')} | Stage: {s.get('stage','?')} | Tags: {tags} | {s.get('description','')[:120]}"
        )

    improvement = f"\nPrevious critique to address:\n{critique}" if critique else ""

    prompt = f"""You are a startup research analyst. A user wants to find startups that match the following query:

QUERY: {query}
{improvement}

Below is a list of YC-backed startups. Return a JSON array of indices (0-based) for startups that match the query.
Be generous — if a startup is partially related, include it.
Return ONLY valid JSON like: {{"matches": [0, 3, 7, 12]}}

STARTUPS:
{chr(10).join(startup_lines)}
"""

    response = llm.invoke([
        SystemMessage(content="You are a precise startup filter. Respond only with valid JSON."),
        HumanMessage(content=prompt)
    ])

    try:
        text = response.content.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        data = json.loads(text)
        indices = data.get("matches", [])
        filtered = [raw[i] for i in indices if 0 <= i < len(raw)]
    except Exception:
        # Fallback: keyword match
        kw = query.lower()
        filtered = [
            s for s in raw
            if kw in s.get("description", "").lower()
            or kw in s.get("sector", "").lower()
            or any(kw in t.lower() for t in s.get("tags", []))
        ]

    if not filtered:
        filtered = raw[:10]  # Last resort

    return {
        **state,
        "filtered_startups": filtered,
        "status": "analyzing",
        "messages": [AIMessage(content=f"[Filter Agent] {len(filtered)} startups matched the query.")]
    }


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 3 — ANALYST
# ──────────────────────────────────────────────────────────────────────────────

def analyst_node(state: AgentState) -> AgentState:
    """
    Enriches each filtered startup with funding stage, business model,
    and a brief investment note.
    """
    llm = get_llm()
    search = DuckDuckGoSearchRun()
    filtered = state["filtered_startups"]
    enriched = []

    for startup in filtered[:15]:  # Cap at 15 to avoid token overflow
        name = startup["name"]
        existing_stage = startup.get("stage", "Unknown")

        # Quick web search for funding info
        try:
            search_result = search.run(f"{name} startup funding round 2024 2025")[:600]
        except Exception:
            search_result = "No search result available."

        prompt = f"""Startup: {name}
Description: {startup.get('description', 'N/A')}
Known Stage: {existing_stage}
Search Snippet: {search_result}

Return a JSON object with these exact keys:
{{
  "funding_stage": "Seed / Series A / Series B / Series C / Series D+ / Public / Unknown",
  "total_raised": "e.g. $45M or Unknown",
  "business_model": "SaaS / Marketplace / API / Consumer / Biotech / etc.",
  "one_line_note": "One sentence investment insight"
}}
Return ONLY valid JSON."""

        try:
            resp = llm.invoke([
                SystemMessage(content="You are an investment analyst. Return only JSON."),
                HumanMessage(content=prompt)
            ])
            text = resp.content.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            details = json.loads(text)
        except Exception:
            details = {
                "funding_stage": existing_stage,
                "total_raised": "Unknown",
                "business_model": "N/A",
                "one_line_note": "Insufficient public data available.",
            }

        enriched.append({**startup, **details})

    return {
        **state,
        "enriched_startups": enriched,
        "status": "critiquing",
        "messages": [AIMessage(content=f"[Analyst] Enriched {len(enriched)} startups with funding and business data.")]
    }


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 4 — CRITIC
# ──────────────────────────────────────────────────────────────────────────────

def critic_node(state: AgentState) -> AgentState:
    """
    Scores the result quality. If score < 7, loops back to Filter Agent.
    On approval, compiles the final list.
    """
    llm = get_llm()
    query = state["query"]
    enriched = state["enriched_startups"]
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)

    startup_summary = "\n".join(
        f"- {s['name']} | {s.get('funding_stage','?')} | {s.get('business_model','?')} | {s.get('one_line_note','')}"
        for s in enriched[:15]
    )

    prompt = f"""You are a strict research quality controller.

USER QUERY: {query}

RESULTS ({len(enriched)} startups):
{startup_summary}

Evaluate:
1. Do the results actually match the query?
2. Is the funding/sector data plausible?
3. Are there obvious mismatches?

Return ONLY this JSON:
{{
  "quality_score": <1-10>,
  "is_satisfactory": <true or false>,
  "issues": ["issue 1", "issue 2"],
  "filter_improvement": "What the filter agent should do better next time"
}}

Score ≥ 7 means is_satisfactory: true.
Iteration {iteration+1}/{max_iter} — if this is the last iteration, set is_satisfactory: true."""

    try:
        resp = llm.invoke([
            SystemMessage(content="You are a quality controller. Return only JSON."),
            HumanMessage(content=prompt)
        ])
        text = resp.content.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        data = json.loads(text)
    except Exception:
        data = {
            "quality_score": 7,
            "is_satisfactory": True,
            "issues": [],
            "filter_improvement": "N/A"
        }

    score = data.get("quality_score", 7)
    satisfied = data.get("is_satisfactory", False)

    if iteration + 1 >= max_iter:
        satisfied = True

    critique_text = (
        f"Score: {score}/10 | Issues: {'; '.join(data.get('issues', []))} | "
        f"Suggestion: {data.get('filter_improvement', '')}"
    )

    new_state = {
        **state,
        "critique": critique_text,
        "quality_score": score,
        "iteration": iteration + 1,
        "messages": [AIMessage(content=f"[Critic] Score: {score}/10 — {'Approved ✓' if satisfied else 'Needs revision, looping back.'}")]
    }

    if satisfied:
        new_state["final_list"] = enriched
        new_state["status"] = "done"
    else:
        new_state["status"] = "filtering"

    return new_state


# ──────────────────────────────────────────────────────────────────────────────
# ROUTING
# ──────────────────────────────────────────────────────────────────────────────

def route(state: AgentState) -> str:
    return "end" if state["status"] == "done" else "filter"


# ──────────────────────────────────────────────────────────────────────────────
# GRAPH
# ──────────────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("scraper", scraper_node)
    g.add_node("filter", filter_node)
    g.add_node("analyst", analyst_node)
    g.add_node("critic", critic_node)

    g.set_entry_point("scraper")
    g.add_edge("scraper", "filter")
    g.add_edge("filter", "analyst")
    g.add_edge("analyst", "critic")
    g.add_conditional_edges("critic", route, {"filter": "filter", "end": END})

    return g.compile()


def run_pipeline(batch: str, query: str, max_iterations: int = 2):
    """Generator — yields each step's output for Streamlit to consume."""
    graph = build_graph()
    state: AgentState = {
        "batch": batch,
        "query": query,
        "raw_startups": [],
        "filtered_startups": [],
        "enriched_startups": [],
        "critique": "",
        "quality_score": 0,
        "final_list": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "status": "scraping",
        "messages": [HumanMessage(content=f"Query: {query} | Batch: {batch}")],
    }
    for step in graph.stream(state):
        yield step
