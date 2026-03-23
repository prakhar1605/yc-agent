"""
YC Startup Research Agent - Streamlit UI
=========================================
Clean, professional interface for the multi-agent research system.
"""

import streamlit as st
import time
import os
from datetime import datetime

# ─────────────────────────────────────────
# PAGE CONFIG - Sabse pehle set karo
# ─────────────────────────────────────────

st.set_page_config(
    page_title="YC Research Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0a0f 100%);
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 15, 30, 0.95) !important;
        border-right: 1px solid rgba(99, 179, 237, 0.2);
    }
    .agent-card {
        background: rgba(20, 20, 40, 0.8);
        border: 1px solid rgba(99, 179, 237, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
    }
    .agent-card.active {
        border-color: rgba(99, 179, 237, 0.7);
        box-shadow: 0 0 20px rgba(99, 179, 237, 0.15);
    }
    .agent-card.done {
        border-color: rgba(72, 199, 142, 0.5);
    }
    .main-header {
        text-align: center;
        padding: 20px 0 10px;
    }
    .main-header h1 {
        font-size: 2.5rem;
        background: linear-gradient(90deg, #63b3ed, #b794f4, #63b3ed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% auto;
        animation: shine 3s linear infinite;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-active {
        background: rgba(99, 179, 237, 0.2);
        color: #63b3ed;
        border: 1px solid rgba(99, 179, 237, 0.4);
    }
    .badge-done {
        background: rgba(72, 199, 142, 0.2);
        color: #48c78e;
        border: 1px solid rgba(72, 199, 142, 0.4);
    }
    .badge-waiting {
        background: rgba(160, 160, 160, 0.1);
        color: #888;
        border: 1px solid rgba(160, 160, 160, 0.2);
    }
    .report-container {
        background: rgba(20, 25, 45, 0.9);
        border: 1px solid rgba(183, 148, 244, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    [data-testid="metric-container"] {
        background: rgba(20, 20, 40, 0.6);
        border: 1px solid rgba(99, 179, 237, 0.15);
        border-radius: 10px;
        padding: 10px;
    }
    [data-testid="stExpander"] {
        background: rgba(15, 15, 30, 0.6);
        border: 1px solid rgba(99, 179, 237, 0.15);
        border-radius: 8px;
    }
    #MainMenu, footer { visibility: hidden; }
    .stButton > button {
        background: linear-gradient(135deg, #4a7bbd, #7c5cbf);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a8bcd, #8c6ccf);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 179, 237, 0.3);
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SIDEBAR - Settings
# ─────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    st.markdown("### 🔑 API Key")
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-...",
        help="OpenRouter API key. Get it from openrouter.ai",
        key="api_key_input"
    )

    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if api_key:
            st.success("✅ API key loaded from environment")

    st.markdown("### 🤖 Model Selection")
    model_options = {
        "Claude 3.5 Haiku (Fast & Cheap)": "anthropic/claude-3.5-haiku",
        "Claude 3.5 Sonnet (Balanced)": "anthropic/claude-3.5-sonnet",
        "GPT-4o Mini (Fast)": "openai/gpt-4o-mini",
        "Gemini Flash 1.5 (Fast)": "google/gemini-flash-1.5",
        "Llama 3.1 70B (Free)": "meta-llama/llama-3.1-70b-instruct:free",
    }
    selected_model_name = st.selectbox(
        "Choose Model",
        list(model_options.keys()),
        index=0
    )
    selected_model = model_options[selected_model_name]

    st.markdown("### 🔄 Research Depth")
    max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=4,
        value=2,
        help="Critic kitni baar loop chalayega. Zyada = better quality, slow speed"
    )

    st.markdown("---")
    st.markdown("### 📊 About This System")
    st.markdown("""
    **3 AI Agents working together:**
    
    🔍 **Searcher**  
    Web se latest startup data laata hai
    
    📈 **Investment Analyst**  
    Funding & business model analyze karta hai
    
    🎯 **Critic**  
    Quality check karta hai, loop decide karta hai
    
    **LangGraph Powers:**
    - Conditional Edges
    - Self-Correction Loops
    - Shared State Management
    """)

    st.markdown("---")
    st.markdown("### 💡 Sample Topics")
    sample_topics = [
        "AI coding assistants (Cursor, Windsurf)",
        "Fintech startups India 2024",
        "B2B SaaS vertical AI agents",
        "Climate tech startups Series A",
        "Developer tools YC W25",
    ]
    for topic in sample_topics:
        if st.button(f"📌 {topic}", key=f"sample_{topic}"):
            st.session_state.topic_input = topic


# ─────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🚀 YC Startup Research Agent</h1>
    <p style="color: #888; font-size: 1.1rem;">Multi-Agent AI System | LangGraph Powered | Self-Correcting</p>
</div>
""", unsafe_allow_html=True)

with st.expander("🔗 Agent Architecture (Click to expand)", expanded=False):
    col1, col2, col3, col4, col5 = st.columns([2, 0.5, 2, 0.5, 2])
    with col1:
        st.markdown("""
        <div class="agent-card">
            <h4>🔍 Searcher</h4>
            <p style="color: #aaa; font-size: 0.85rem;">DuckDuckGo search<br>Query refinement<br>Data structuring</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align:center; padding-top: 30px; font-size: 1.5rem; color: #63b3ed;'>→</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agent-card">
            <h4>📈 Analyst</h4>
            <p style="color: #aaa; font-size: 0.85rem;">Business model analysis<br>Funding evaluation<br>Market assessment</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='text-align:center; padding-top: 30px; font-size: 1.5rem; color: #63b3ed;'>→</div>", unsafe_allow_html=True)
    with col5:
        st.markdown("""
        <div class="agent-card">
            <h4>🎯 Critic</h4>
            <p style="color: #aaa; font-size: 0.85rem;">Quality scoring<br>Gap identification<br>Loop/End decision</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; margin-top: 10px; color: #888;'>
        <span style='color: #f6ad55;'>⚡ Conditional Edge:</span> Critic → (Score < 7) → Searcher (loop) | (Score ≥ 7) → Final Report
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────
# INPUT SECTION
# ─────────────────────────────────────────

col_input, col_btn = st.columns([5, 1])
with col_input:
    topic = st.text_input(
        "🔍 Research Topic",
        placeholder="e.g., 'AI agents for enterprise', 'Indian fintech startups 2025', 'YC W25 batch'",
        key="topic_input",
        label_visibility="collapsed"
    )

with col_btn:
    start_research = st.button("🚀 Research!", use_container_width=True)

# ─────────────────────────────────────────
# RESEARCH EXECUTION
# ─────────────────────────────────────────

if start_research:
    if not api_key:
        st.error("❌ OpenRouter API key required! Sidebar mein enter karo.")
        st.stop()

    if not topic or len(topic.strip()) < 3:
        st.error("❌ Research topic enter karo (minimum 3 characters).")
        st.stop()

    try:
        from agents import run_research
    except ImportError as e:
        st.error(f"❌ agents.py import error: {e}")
        st.error("Make sure agents.py same directory mein hai.")
        st.stop()

    st.session_state.research_complete = False
    st.session_state.final_report = ""
    st.session_state.all_iterations = []

    st.markdown("### 📡 Live Research Progress")

    agent_cols = st.columns(3)
    with agent_cols[0]:
        searcher_status = st.empty()
    with agent_cols[1]:
        analyst_status = st.empty()
    with agent_cols[2]:
        critic_status = st.empty()

    def show_agent(placeholder, icon, name, status="waiting", detail=""):
        colors = {"waiting": "#888", "active": "#63b3ed", "done": "#48c78e"}
        badges = {"waiting": "badge-waiting", "active": "badge-active", "done": "badge-done"}
        badge_text = {"waiting": "WAITING", "active": "RUNNING...", "done": "DONE ✓"}
        color = colors.get(status, "#888")
        placeholder.markdown(f"""
        <div class="agent-card {'active' if status == 'active' else 'done' if status == 'done' else ''}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.2rem;">{icon} <strong style="color: {color};">{name}</strong></span>
                <span class="status-badge {badges[status]}">{badge_text[status]}</span>
            </div>
            {f'<p style="color: #aaa; font-size: 0.8rem; margin-top: 6px;">{detail}</p>' if detail else ''}
        </div>
        """, unsafe_allow_html=True)

    show_agent(searcher_status, "🔍", "Searcher", "waiting")
    show_agent(analyst_status, "📈", "Analyst", "waiting")
    show_agent(critic_status, "🎯", "Critic", "waiting")

    progress_bar = st.progress(0)
    status_text = st.empty()

    all_steps = []
    current_iteration = 0
    iteration_data = {}

    try:
        show_agent(searcher_status, "🔍", "Searcher", "active", "Web search kar raha hai...")
        status_text.info("🔍 Searcher: Web par data dhundh raha hai...")
        progress_bar.progress(10)

        for step_output in run_research(topic.strip(), api_key, selected_model, max_iterations):
            for node_name, state in step_output.items():
                all_steps.append((node_name, state))
                iter_num = state.get("iteration", 0)

                if node_name == "searcher":
                    current_iteration = iter_num + 1
                    show_agent(searcher_status, "🔍", "Searcher", "active", f"Iteration {current_iteration}: Search complete")
                    show_agent(analyst_status, "📈", "Analyst", "active", "Analysis kar raha hai...")
                    show_agent(critic_status, "🎯", "Critic", "waiting")
                    progress = min(10 + (current_iteration - 1) * 25 + 5, 85)
                    progress_bar.progress(progress)
                    status_text.info(f"📊 Iteration {current_iteration}: Analyst business model analyze kar raha hai...")
                    if iter_num not in iteration_data:
                        iteration_data[iter_num] = {}
                    iteration_data[iter_num]["search"] = state.get("search_results", "")

                elif node_name == "analyst":
                    show_agent(analyst_status, "📈", "Analyst", "done", "Analysis complete!")
                    show_agent(critic_status, "🎯", "Critic", "active", "Quality review kar raha hai...")
                    progress = min(10 + (current_iteration - 1) * 25 + 15, 90)
                    progress_bar.progress(progress)
                    status_text.info(f"🎯 Iteration {current_iteration}: Critic quality check kar raha hai...")
                    if iter_num not in iteration_data:
                        iteration_data[iter_num] = {}
                    iteration_data[iter_num]["analysis"] = state.get("analysis", "")

                elif node_name == "critic":
                    critique = state.get("critique", "")
                    final_report = state.get("final_report", "")
                    status_val = state.get("status", "")
                    if iter_num not in iteration_data:
                        iteration_data[iter_num] = {}
                    iteration_data[iter_num]["critique"] = critique

                    if status_val == "done" or final_report:
                        show_agent(searcher_status, "🔍", "Searcher", "done", "Complete!")
                        show_agent(analyst_status, "📈", "Analyst", "done", "Complete!")
                        show_agent(critic_status, "🎯", "Critic", "done", "Approved! ✅")
                        progress_bar.progress(100)
                        status_text.success("✅ Research complete! Report ready.")
                        st.session_state.final_report = final_report
                        st.session_state.research_complete = True
                        st.session_state.all_iterations = iteration_data
                        st.session_state.total_iterations = current_iteration
                    else:
                        show_agent(searcher_status, "🔍", "Searcher", "active", "Refined search kar raha hai...")
                        show_agent(analyst_status, "📈", "Analyst", "waiting")
                        show_agent(critic_status, "🎯", "Critic", "done", f"Loop #{current_iteration}")
                        status_text.warning(f"🔄 Iteration {current_iteration} complete. More research needed...")

    except Exception as e:
        st.error(f"❌ Research error: {str(e)}")
        st.exception(e)
        st.stop()

# ─────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────

if st.session_state.get("research_complete") and st.session_state.get("final_report"):

    st.markdown("---")
    st.markdown("## 📊 Research Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔄 Iterations Run", st.session_state.get("total_iterations", "N/A"))
    with col2:
        st.metric("📝 Report Generated", "✅ Yes")
    with col3:
        st.metric("⏰ Completed At", datetime.now().strftime("%H:%M:%S"))

    st.markdown("### 📋 Final Research Report")
    st.markdown(f"""
    <div class="report-container">
        {st.session_state.final_report.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        label="⬇️ Download Report (TXT)",
        data=st.session_state.final_report,
        file_name=f"yc_research_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.session_state.get("all_iterations"):
        st.markdown("### 🔬 Research Process Details")
        iter_data = st.session_state.all_iterations
        tabs = st.tabs([f"Iteration {i+1}" for i in range(len(iter_data))])

        for idx, tab in enumerate(tabs):
            with tab:
                data = iter_data.get(idx, {})
                tab_col1, tab_col2 = st.columns(2)
                with tab_col1:
                    with st.expander("🔍 Search Results", expanded=False):
                        st.markdown(data.get("search", "No data"), unsafe_allow_html=False)
                    with st.expander("📈 Investment Analysis", expanded=False):
                        st.markdown(data.get("analysis", "No data"), unsafe_allow_html=False)
                with tab_col2:
                    with st.expander("🎯 Critic Feedback", expanded=True):
                        st.markdown(data.get("critique", "No data"))

elif not st.session_state.get("research_complete"):
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #666;">
        <div style="font-size: 3rem;">🔍</div>
        <h3 style="color: #888;">Ready to Research</h3>
        <p>Topic enter karo aur <strong>Research!</strong> button dabao</p>
        <p style="font-size: 0.85rem;">Sidebar mein sample topics mein se choose kar sakte ho</p>
    </div>
    """, unsafe_allow_html=True)
