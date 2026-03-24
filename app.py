import streamlit as st
import pandas as pd
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import run_extraction, build_graph
from state import AgentState

# ─── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Email Extractor",
    page_icon="📧",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
.big-title { font-size: 2.2rem; font-weight: 700; margin-bottom: 0; }
.subtitle  { color: #888; font-size: 1rem; margin-top: 0; }
.agent-log { background: #1e1e2e; color: #cdd6f4; padding: 12px 16px;
             border-radius: 8px; font-family: monospace; font-size: 0.85rem; }
.confidence-high   { background:#d1fae5; color:#065f46; padding:2px 8px; border-radius:12px; font-size:0.8rem; }
.confidence-medium { background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:12px; font-size:0.8rem; }
.confidence-low    { background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:12px; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────
st.markdown('<p class="big-title">📧 Agentic Email Extractor</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by LangGraph + Claude + OpenRouter (Perplexity)</p>', unsafe_allow_html=True)
st.divider()

# ─── Sidebar: API Keys ────────────────────────────────────────
with st.sidebar:
    st.header("🔑 API Keys")
    anthropic_key = st.text_input("Anthropic API Key", type="password",
                                   value=os.getenv("ANTHROPIC_API_KEY", ""))
    openrouter_key = st.text_input("OpenRouter API Key", type="password",
                                    value=os.getenv("OPENROUTER_API_KEY", ""))

    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key

    st.divider()
    st.header("📋 Mode")
    mode = st.radio("Select Mode", ["Single Search", "Batch (CSV Upload)"])

    st.divider()
    st.markdown("**Agent Pipeline:**")
    st.markdown("1. 🔍 Web Search Agent")
    st.markdown("2. 🟠 YC Directory Agent")
    st.markdown("3. 🌐 Website Scraper Agent")
    st.markdown("4. 🤖 Email Guesser (Claude)")
    st.markdown("5. ✅ Validator Agent")

# ─── Main Area ────────────────────────────────────────────────

if mode == "Single Search":
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("🏢 Company Name", placeholder="e.g. Stripe, Airbnb, Linear")
    with col2:
        founder_name = st.text_input("👤 Founder Name (optional)", placeholder="e.g. Patrick Collison")

    run_btn = st.button("🚀 Extract Emails", type="primary", use_container_width=True)

    if run_btn:
        if not company_name:
            st.error("Please enter a company name!")
        elif not anthropic_key or not openrouter_key:
            st.error("Please enter both API keys in the sidebar!")
        else:
            # ── Progress display ──
            progress_bar = st.progress(0, text="Starting agents...")
            log_box = st.empty()
            logs = []

            steps = [
                (0.1,  "🔍 Web Search Agent running..."),
                (0.30, "🟠 YC Directory Agent scraping..."),
                (0.55, "🌐 Website Scraper running..."),
                (0.75, "🤖 Claude Email Guesser running..."),
                (0.90, "✅ Validator Agent checking emails..."),
                (1.0,  "🎉 Done!"),
            ]

            # Animate progress while running
            results_placeholder = st.empty()

            with st.spinner("Agents are working... this may take 30-60 seconds"):
                # Run actual extraction
                try:
                    final_state = run_extraction(company_name, founder_name)
                except Exception as e:
                    st.error(f"Pipeline error: {str(e)}")
                    st.stop()

            # Show full progress after completion
            for prog, msg in steps:
                progress_bar.progress(prog, text=msg)
                time.sleep(0.2)

            # ── Show logs ──
            st.subheader("📜 Agent Logs")
            log_html = '<div class="agent-log">'
            for msg in final_state.get("messages", []):
                log_html += f"{msg}<br>"
            if final_state.get("errors"):
                for err in final_state["errors"]:
                    log_html += f'<span style="color:#f38ba8">⚠️ {err}</span><br>'
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

            # ── Show results ──
            final_emails = final_state.get("final_emails", [])
            st.divider()

            if not final_emails:
                st.warning("😔 No emails found. Try a different company name or check your API keys.")
            else:
                st.subheader(f"📧 Found {len(final_emails)} Emails")

                # Build DataFrame
                df = pd.DataFrame(final_emails)
                df.columns = [c.capitalize() for c in df.columns]

                # Color-coded confidence
                def highlight_conf(val):
                    colors = {"high": "background-color: #d1fae5",
                              "medium": "background-color: #fef3c7",
                              "low": "background-color: #fee2e2"}
                    return colors.get(val.lower(), "")

                styled_df = df.style.applymap(highlight_conf, subset=["Confidence"])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # ── Download buttons ──
                col_a, col_b = st.columns(2)
                with col_a:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download CSV",
                        data=csv,
                        file_name=f"{company_name.lower().replace(' ', '_')}_emails.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_b:
                    emails_only = "\n".join([e["email"] for e in final_emails])
                    st.download_button(
                        "⬇️ Download Emails Only (.txt)",
                        data=emails_only,
                        file_name=f"{company_name.lower().replace(' ', '_')}_emails.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                # ── Stats ──
                st.divider()
                st.subheader("📊 Stats")
                c1, c2, c3, c4 = st.columns(4)
                high = sum(1 for e in final_emails if e["confidence"] == "high")
                med  = sum(1 for e in final_emails if e["confidence"] == "medium")
                low  = sum(1 for e in final_emails if e["confidence"] == "low")
                c1.metric("Total Emails", len(final_emails))
                c2.metric("🟢 High Confidence", high)
                c3.metric("🟡 Medium Confidence", med)
                c4.metric("🔴 Low Confidence", low)

# ─── Batch Mode ───────────────────────────────────────────────
else:
    st.subheader("📁 Batch Mode — Upload CSV")
    st.markdown("CSV must have a `company` column. Optional: `founder` column.")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded:
        df_input = pd.read_csv(uploaded)
        st.write("Preview:", df_input.head())

        if "company" not in df_input.columns:
            st.error("CSV must have a 'company' column!")
        else:
            run_batch = st.button("🚀 Run Batch Extraction", type="primary")

            if run_batch:
                if not anthropic_key or not openrouter_key:
                    st.error("Please enter both API keys in the sidebar!")
                else:
                    all_results = []
                    progress = st.progress(0)
                    status = st.empty()

                    for i, row in df_input.iterrows():
                        company = row["company"]
                        founder = row.get("founder", "") if "founder" in df_input.columns else ""
                        status.text(f"Processing {i+1}/{len(df_input)}: {company}")

                        try:
                            result = run_extraction(str(company), str(founder) if founder else "")
                            for email in result.get("final_emails", []):
                                all_results.append({
                                    "company": company,
                                    **email
                                })
                        except Exception as e:
                            st.warning(f"Failed for {company}: {e}")

                        progress.progress((i + 1) / len(df_input))

                    status.text("✅ Batch complete!")

                    if all_results:
                        df_out = pd.DataFrame(all_results)
                        st.dataframe(df_out, use_container_width=True)
                        st.download_button(
                            "⬇️ Download All Results",
                            data=df_out.to_csv(index=False),
                            file_name="batch_emails.csv",
                            mime="text/csv"
                        )