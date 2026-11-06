from pathlib import Path
import json
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PromoFinder — Microdrama Promo Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 PromoFinder: AI Promo Moment Selector")
st.markdown("Automated discovery and scoring of 20–60s viral promo clips across 50 screenplay episodes.")

out_dir = Path("out")
json_path = out_dir / "promos.json"

if not json_path.exists():
    st.error("No promo outputs found in `out/promos.json`. Run `python -m promofinder.cli` first.")
    st.stop()

with open(json_path, "r", encoding="utf-8") as f:
    promos = json.load(f)

# Metrics summary
col1, col2, col3, col4 = st.columns(4)
col1.metric("Episodes Evaluated", "50")
col2.metric("Raw Candidates Scanned", "13,568")
col3.metric("Passed Hard Filter", "9,954")
col4.metric("Top Ranked Promos", len(promos))

st.divider()

# Sidebar filters
st.sidebar.header("Filter Promos")
tier_filter = st.sidebar.multiselect(
    "Select Tiers",
    options=["POST_FIRST", "STRONG", "BACKUP"],
    default=["POST_FIRST", "STRONG", "BACKUP"]
)

min_score = st.sidebar.slider("Minimum Final Score", 0.0, 1.0, 0.50, 0.01)

filtered_promos = [
    p for p in promos
    if p["tier"] in tier_filter and p["scores"]["final"] >= min_score
]

# Table view
st.subheader("📋 Ranked Promo Moments")
table_data = []
for p in filtered_promos:
    s0 = p["segments"][0]
    table_data.append({
        "Rank": p["rank"],
        "Tier": p["tier"],
        "Episode": f"Ep {s0['episode']}",
        "Start": s0["start"],
        "End": s0["end"],
        "Duration": f"{p['duration_sec']}s",
        "Final Score": f"{p['scores']['final']:.2f}",
        "Hook Score": f"{p['scores']['hook']:.2f}",
        "Cliffhanger Score": f"{p['scores']['cliffhanger']:.2f}",
        "Clarity": f"{p['scores']['clarity']:.2f}",
    })

if table_data:
    st.dataframe(pd.DataFrame(table_data), use_container_width=True)
else:
    st.warning("No promos match the current filter.")

st.divider()

# Deep Dive Cards
st.subheader("🔍 Promo Deep Dive & Moment Breakdown")
for p in filtered_promos:
    s0 = p["segments"][0]
    with st.expander(f"Rank {p['rank']} — Episode {s0['episode']} [{s0['start']} to {s0['end']}] — {p['tier']}"):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"**⚡ Hook (First 3s):**")
            st.info(p["hook"])
            st.markdown(f"**🧗 Cliffhanger Cut Point:**")
            st.warning(p["cliffhanger"])
            st.markdown(f"**💡 Why It Works:** {p['why_it_works']}")
        with c2:
            st.markdown("**Feature Scores:**")
            st.write(f"- Final Score: **{p['scores']['final']}**")
            st.write(f"- Hook: `{p['scores']['hook']}`")
            st.write(f"- Cliffhanger: `{p['scores']['cliffhanger']}`")
            st.write(f"- Clarity: `{p['scores']['clarity']}`")
            st.write(f"- Intensity: `{p['scores']['intensity']}`")
            st.write(f"- Spoiler Risk: `{p['scores']['spoiler_risk']}`")
