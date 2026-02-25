import streamlit as st
import pandas as pd
import plotly.express as px
import utils
import os

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ByteMind Ltd | Strategic Tax Intelligence",
    page_icon="assets/images/profile_dr_zhang.png", 
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Custom CSS
utils.load_css()

# -----------------------------------------------------------------------------
# HERO SECTION
# -----------------------------------------------------------------------------
# Using a container for better control over the hero layout
with st.container():
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Smarter Tax Strategy<br>for Global Growth.</h1>', unsafe_allow_html=True)
    st.markdown(
        """
        <p class="hero-subtitle">
        Expanding your business overseas? Don't let tax compliance eat your profits.<br>
        ByteMind combines <strong>academic rigour</strong> with <strong>practical consulting</strong> to help New Zealand SMEs and Tech Exporters grow safely.
        </p>
        """,
        unsafe_allow_html=True
    )
    
    col_cta1, col_cta2, col_cta3 = st.columns([1, 1, 1])
    with col_cta2:
        if st.button("Explore Our Services", use_container_width=True):
            st.switch_page("pages/1_Services.py")
            
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PREVIEW CHART (The "Byte")
# -----------------------------------------------------------------------------
st.markdown("## The Data Advantage")
st.write("We don't just give advice; we back it up with proprietary data.")

try:
    df_tefi = pd.read_csv("data/tefi_raw.csv")
    fig = px.bar(
        df_tefi.sort_values("TEFI Score (0-100)"), 
        x="Country", 
        y="TEFI Score (0-100)", 
        color="TEFI Score (0-100)",
        title="Tech Export Friction Index (TEFI) - 2026 Preview",
        color_continuous_scale=["#E2E8F0", "#3B82F6", "#1E40AF"], # Professional Blues
    )
    fig.update_layout(
        height=400, 
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="white",
        font=dict(family="Plus Jakarta Sans", size=12, color="#334155")
    )
    st.plotly_chart(fig, use_container_width=True)
except FileNotFoundError:
    st.error("TEFI Data not found. Please run data update.")

st.write("")
st.write("")

# -----------------------------------------------------------------------------
# LATEST INSIGHTS (CMS)
# -----------------------------------------------------------------------------
st.markdown("## Latest Insights")
st.write("Analysis of tax policy changes that impact NZ exporters.")

# Simple CMS: Read markdown files from 'posts/'
posts_dir = "posts"
if os.path.exists(posts_dir):
    files = sorted(os.listdir(posts_dir), reverse=True) # Newest first
    
    col1, col2 = st.columns(2)
    
    for i, filename in enumerate(files):
        if filename.endswith(".md"):
            with open(os.path.join(posts_dir, filename), "r") as f:
                content = f.read()
                
            # Simple Frontmatter Parser
            metadata = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]
                    for line in frontmatter.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()
            
            # Display Post Card
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                with st.container():
                    st.markdown(f"### {metadata.get('title', 'Untitled')}")
                    st.caption(f"{metadata.get('date', '')} • {metadata.get('author', 'Dr Zhang')}")
                    st.write(metadata.get('summary', ''))
                    with st.expander("Read More"):
                        st.markdown(body)

st.markdown("---")
st.caption("© 2026 ByteMind Ltd. All Rights Reserved.")
