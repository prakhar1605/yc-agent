"""
YC Startup Research — Streamlit UI
====================================
• Batch selector (slide bar)
• Natural language query box
• Live agent activity feed
• Results as a clean startup list
• API key loaded from .env / environment
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env automatically

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="YC Startup Research",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #f5f2eb !important;
    font-family: 'DM Sans', sans-serif;
    color: #1a1611;
}

[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, header { visibility: hidden; }

.block-container {
    max-width: 1100px !important;
    padding: 48px 32px 80px !important;
}

/* ── Hero ── */
.hero {
    margin-bottom: 52px;
}
.hero-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #8a7e6e;
    margin-bottom: 14px;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    line-height: 1.1;
    color: #1a1611;
    margin-bottom: 16px;
}
.hero-title em {
    font-style: italic;
    color: #c85c1a;
}
.hero-sub {
    font-size: 1rem;
    color: #6b5e4e;
    max-width: 520px;
    line-height: 1.6;
}

/* ── Batch selector ── */
.batch-section { margin-bottom: 36px; }
.batch-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #8a7e6e;
    margin-bottom: 12px;
}
.batch-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.chip {
    display: inline-block;
    padding: 7px 18px;
    border-radius: 99px;
    border: 1.5px solid #c9bfaf;
    background: transparent;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    color: #5a4e3e;
    cursor: pointer;
    transition: all 0.18s ease;
    letter-spacing: 0.5px;
}
.chip:hover { border-color: #c85c1a; color: #c85c1a; }
.chip.selected {
    background: #c85c1a;
    border-color: #c85c1a;
    color: #fff;
}

/* ── Query box ── */
.stTextArea textarea {
    background: #fffdf8 !important;
    border: 1.5px solid #c9bfaf !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    color: #1a1611 !important;
    padding: 16px !important;
    resize: none !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease !important;
}
.stTextArea textarea:focus {
    border-color: #c85c1a !important;
    box-shadow: 0 0 0 3px rgba(200,92,26,0.08) !important;
}
.stTextArea label {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase !important;
    color: #8a7e6e !important;
    margin-bottom: 8px !important;
}

/* ── Run button ── */
.stButton > button {
    background: #1a1611 !important;
    color: #f5f2eb !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 13px 32px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    width: auto !important;
}
.stButton > button:hover {
    background: #c85c1a !important;
    transform: translateY(-1px) !important;
}

/* ── Agent feed ── */
.agent-feed {
    background: #1a1611;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 28px 0 20px;
    min-height: 120px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    line-height: 1.8;
}
.feed-header {
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #5a5040;
    margin-bottom: 14px;
}
.feed-line { color: #a89880; }
.feed-line.active { color: #f5c87a; }
.feed-line.done { color: #6fcf97; }
.feed-line.error { color: #f28b82; }

/* ── Agent status bars ── */
.agent-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-radius: 10px;
    margin: 5px 0;
    background: #fffdf8;
    border: 1.5px solid #e8e0d4;
    transition: all 0.2s ease;
}
.agent-row.active {
    border-color: #c85c1a;
    background: #fff9f5;
}
.agent-row.done {
    border-color: #6fcf97;
    background: #f5fff8;
}
.agent-dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #c9bfaf;
    flex-shrink: 0;
}
.agent-dot.active { background: #c85c1a; animation: pulse 1s infinite; }
.agent-dot.done { background: #6fcf97; }
@keyframes pulse {
    0%,100% { opacity: 1; } 50% { opacity: 0.3; }
}
.agent-name {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    color: #3a2e20;
    min-width: 120px;
}
.agent-desc { font-size: 13px; color: #6b5e4e; flex: 1; }
.agent-badge {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 99px;
    letter-spacing: 1px;
}
.badge-wait { background: #ede8de; color: #8a7e6e; }
.badge-run  { background: #fde8d8; color: #c85c1a; }
.badge-done { background: #d8f5e5; color: #2d9e5a; }

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #c9bfaf 20%, #c9bfaf 80%, transparent);
    margin: 36px 0;
}

/* ── Result header ── */
.result-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 24px;
}
.result-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: #1a1611;
}
.result-count {
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    color: #8a7e6e;
}

/* ── Startup cards ── */
.startup-card {
    background: #fffdf8;
    border: 1.5px solid #e0d8cc;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 14px;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.startup-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: #c85c1a;
    border-radius: 3px 0 0 3px;
}
.startup-card:hover {
    border-color: #c85c1a;
    transform: translateX(3px);
    box-shadow: -3px 4px 16px rgba(200,92,26,0.08);
}
.card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 8px;
}
.card-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.2rem;
    color: #1a1611;
}
.card-stage {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 99px;
    background: #f0ebe0;
    color: #5a4e3e;
    white-space: nowrap;
}
.card-stage.series-b { background: #ddf0e8; color: #1a6640; }
.card-stage.series-c { background: #d8e8ff; color: #1a3d80; }
.card-stage.series-d { background: #efe0ff; color: #5a1a80; }
.card-stage.public { background: #fff0d0; color: #805a1a; }
.card-desc {
    font-size: 13.5px;
    color: #5a4e3e;
    line-height: 1.55;
    margin-bottom: 12px;
}
.card-note {
    font-size: 13px;
    color: #8a7e6e;
    font-style: italic;
    line-height: 1.5;
    margin-bottom: 14px;
}
.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}
.meta-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10.5px;
    padding: 3px 10px;
    border-radius: 6px;
    background: #ede8de;
    color: #5a4e3e;
    letter-spacing: 0.3px;
}
.meta-raised {
    font-family: 'DM Mono', monospace;
    font-size: 10.5px;
    color: #2d9e5a;
    font-weight: 600;
    margin-left: auto;
}
.card-link {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #c85c1a;
    text-decoration: none;
    margin-top: 4px;
    display: inline-block;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #8a7e6e;
}
.empty-state .big { font-size: 2.5rem; margin-bottom: 16px; }
.empty-state p { font-size: 14px; line-height: 1.7; }

/* ── Streamlit overrides ── */
div[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
.stProgress > div > div { background: #c85c1a !important; border-radius: 99px !important; }
.stProgress { background: #e8e0d4 !important; border-radius: 99px !important; }
</style>
""", unsafe_allow_html=True)


# ── Session defaults ───────────────────────────────────────────────────────────

if "selected_batch" not in st.session_state:
    st.session_state.selected_batch = "All"
if "results" not in st.session_state:
    st.session_state.results = []
if "done" not in st.session_state:
    st.session_state.done = False


# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <div class="hero-label">Y Combinator · Startup Intelligence</div>
    <h1 class="hero-title">Find startups that<br><em>match your thesis.</em></h1>
    <p class="hero-sub">
        Select a YC batch, describe what you are looking for in plain English,
        and let the research agents do the work.
    </p>
</div>
""", unsafe_allow_html=True)


# ── Batch selector ────────────────────────────────────────────────────────────

BATCHES = ["All", "W25", "S24", "W24", "S23", "W23", "S22", "W22"]

st.markdown('<div class="batch-label">Select Batch</div>', unsafe_allow_html=True)

cols = st.columns(len(BATCHES))
for i, batch in enumerate(BATCHES):
    with cols[i]:
        selected = st.session_state.selected_batch == batch
        label = f"**{batch}**" if selected else batch
        if st.button(batch, key=f"batch_{batch}", use_container_width=True):
            st.session_state.selected_batch = batch
            st.rerun()

# Visual indicator
active = st.session_state.selected_batch
chips_html = "".join(
    f'<span class="chip {"selected" if b == active else ""}">{b}</span>'
    for b in BATCHES
)
st.markdown(f'<div class="batch-chips">{chips_html}</div>', unsafe_allow_html=True)

st.markdown("<div style='margin: 24px 0'></div>", unsafe_allow_html=True)


# ── Query ─────────────────────────────────────────────────────────────────────

query = st.text_area(
    "RESEARCH QUERY",
    placeholder='e.g.  "Give me the name list of startups which have Series B and are in health AI tech"',
    height=90,
    key="query_input",
    label_visibility="visible",
)

st.markdown("<div style='margin: 16px 0'></div>", unsafe_allow_html=True)

run_col, _ = st.columns([1, 4])
with run_col:
    run = st.button("Run Research →", use_container_width=False)


# ── Research pipeline ─────────────────────────────────────────────────────────

AGENT_ICONS = {
    "scraper": "⬡",
    "filter":  "◈",
    "analyst": "◉",
    "critic":  "◎",
}

AGENT_LABELS = {
    "scraper": "Scraper",
    "filter":  "Filter Agent",
    "analyst": "Analyst",
    "critic":  "Critic",
}

AGENT_DESCS = {
    "scraper": "Fetching startups from YC directory",
    "filter":  "Applying your query to narrow results",
    "analyst": "Enriching each startup with funding data",
    "critic":  "Scoring result quality — may loop back",
}

ORDER = ["scraper", "filter", "analyst", "critic"]


def render_agent_row(name: str, status: str, detail: str = ""):
    icon = AGENT_ICONS[name]
    label = AGENT_LABELS[name]
    desc = detail or AGENT_DESCS[name]
    dot_cls = "active" if status == "active" else ("done" if status == "done" else "")
    row_cls = "active" if status == "active" else ("done" if status == "done" else "")
    badge = (
        '<span class="agent-badge badge-run">RUNNING</span>' if status == "active"
        else '<span class="agent-badge badge-done">DONE</span>' if status == "done"
        else '<span class="agent-badge badge-wait">WAITING</span>'
    )
    return f"""
<div class="agent-row {row_cls}">
    <div class="agent-dot {dot_cls}"></div>
    <span class="agent-name">{icon} {label}</span>
    <span class="agent-desc">{desc}</span>
    {badge}
</div>"""


def stage_badge(stage: str) -> str:
    s = stage.lower()
    cls = ""
    if "series b" in s: cls = "series-b"
    elif "series c" in s: cls = "series-c"
    elif "series d" in s or "series e" in s or "series f" in s: cls = "series-d"
    elif "public" in s or "ipo" in s: cls = "public"
    return f'<span class="card-stage {cls}">{stage}</span>'


def render_card(s: dict, idx: int) -> str:
    name = s.get("name", "Unknown")
    desc = s.get("description", "")[:200]
    note = s.get("one_line_note", "")
    stage = s.get("funding_stage") or s.get("stage") or "Unknown"
    raised = s.get("total_raised", "Unknown")
    model = s.get("business_model", "")
    tags = s.get("tags", [])
    url = s.get("url", "#")
    batch = s.get("batch", "")

    tag_html = "".join(f'<span class="meta-tag">{t}</span>' for t in tags[:4])
    if model:
        tag_html += f'<span class="meta-tag">{model}</span>'
    if batch:
        tag_html += f'<span class="meta-tag">{batch}</span>'

    raised_html = f'<span class="meta-raised">↑ {raised}</span>' if raised and raised != "Unknown" else ""

    return f"""
<div class="startup-card">
    <div class="card-top">
        <span class="card-name">{idx}. {name}</span>
        {stage_badge(stage)}
    </div>
    <p class="card-desc">{desc}</p>
    {f'<p class="card-note">"{note}"</p>' if note else ''}
    <div class="card-meta">
        {tag_html}
        {raised_html}
    </div>
    <a class="card-link" href="{url}" target="_blank">↗ {url[:50]}</a>
</div>"""


if run:
    if not query or len(query.strip()) < 5:
        st.error("Please enter a research query.")
        st.stop()

    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        st.error("OPENROUTER_API_KEY not found. Add it to your .env file.")
        st.stop()

    try:
        from agents import run_pipeline
    except ImportError as e:
        st.error(f"Could not import agents.py: {e}")
        st.stop()

    st.session_state.done = False
    st.session_state.results = []

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("**Agent Activity**")

    agent_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_note = st.empty()

    agent_states = {a: "waiting" for a in ORDER}
    agent_details = {a: "" for a in ORDER}

    def refresh_agents():
        html = "".join(
            render_agent_row(a, agent_states[a], agent_details[a])
            for a in ORDER
        )
        agent_placeholder.markdown(html, unsafe_allow_html=True)

    refresh_agents()

    log_lines = []
    log_box = st.empty()

    def push_log(line: str, cls: str = ""):
        log_lines.append(f'<div class="feed-line {cls}">{line}</div>')
        log_box.markdown(
            f'<div class="agent-feed"><div class="feed-header">— live log —</div>'
            + "".join(log_lines[-12:]) + "</div>",
            unsafe_allow_html=True,
        )

    push_log(f"Starting pipeline · batch={st.session_state.selected_batch} · query=\"{query[:60]}...\"")

    PROGRESS_MAP = {
        "scraper": (5, 25),
        "filter":  (25, 55),
        "analyst": (55, 85),
        "critic":  (85, 100),
    }

    try:
        for step in run_pipeline(
            batch=st.session_state.selected_batch,
            query=query.strip(),
            max_iterations=2,
        ):
            for node_name, state in step.items():
                msgs = state.get("messages", [])
                last_msg = msgs[-1].content if msgs else ""

                # Mark previous nodes done
                idx_current = ORDER.index(node_name) if node_name in ORDER else -1
                for prev in ORDER[:idx_current]:
                    agent_states[prev] = "done"

                agent_states[node_name] = "active"
                agent_details[node_name] = ""
                refresh_agents()

                # Progress
                lo, hi = PROGRESS_MAP.get(node_name, (0, 100))
                progress_bar.progress(lo)
                status_note.caption(f"Running {AGENT_LABELS.get(node_name, node_name)}...")
                push_log(last_msg, "active")

                # Completed
                agent_states[node_name] = "done"
                agent_details[node_name] = last_msg.split("]", 1)[-1].strip() if "]" in last_msg else ""
                progress_bar.progress(hi)
                refresh_agents()

                if state.get("status") == "done" and state.get("final_list"):
                    st.session_state.results = state["final_list"]
                    st.session_state.done = True
                    push_log(f"Pipeline complete — {len(state['final_list'])} startups found.", "done")

                elif state.get("status") == "filtering" and node_name == "critic":
                    push_log(f"Critic score: {state.get('quality_score', '?')}/10 — looping back to Filter Agent.", "active")
                    # Reset filter and analyst for re-run visual
                    agent_states["filter"] = "waiting"
                    agent_states["analyst"] = "waiting"
                    refresh_agents()

        progress_bar.progress(100)
        status_note.caption("Research complete.")

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.exception(e)


# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.done and st.session_state.results:
    results = st.session_state.results
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="result-header">'
        f'<span class="result-title">Research Results</span>'
        f'<span class="result-count">{len(results)} startups matched</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for i, s in enumerate(results, 1):
        st.markdown(render_card(s, i), unsafe_allow_html=True)

elif not st.session_state.done:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="empty-state">
        <div class="big">🔬</div>
        <p>Select a YC batch above, describe what you are looking for,<br>
        and press <strong>Run Research</strong> to start the agent pipeline.</p>
    </div>
    """, unsafe_allow_html=True)
