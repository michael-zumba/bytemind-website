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

# Load Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

# -----------------------------------------------------------------------------
# HERO SECTION (Animated & Premium)
# -----------------------------------------------------------------------------
# Using a single container for the hero to ensure vertical stacking alignment
with st.container():
    st.markdown(
        """
        <div class="hero-wrapper animate-fade-in-up">
            <div class="badge">Strategic Tax Intelligence</div>
            <h1 class="hero-title-text">Smarter Tax Strategy<br>for Global Growth</h1>
            <p class="hero-subtitle-text animate-delay-1">
                Combining <strong>academic rigour</strong> with <strong>practical consulting</strong> to help New Zealand SMEs and Exporters navigate complex tax environments.
            </p>
            <div style="margin-top: 2rem;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Call to Action Buttons - Perfectly Centered
    # Using columns with precise ratios to center the button
    c1, c2, c3 = st.columns([1, 0.6, 1])
    with c2:
        if st.button("Explore Our Services", use_container_width=True):
            st.switch_page("pages/1_Services.py")

# -----------------------------------------------------------------------------
# VALUE PROPOSITION / DATA PREVIEW
# -----------------------------------------------------------------------------
st.write("")
st.write("")
st.write("")

# Centered Section Header
st.markdown("<h2 style='text-align: center; margin-bottom: 0.5rem;'>The Data Advantage</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; max-width: 600px; margin: 0 auto; margin-bottom: 3rem;'>We don't just give advice; we back it up with proprietary data. Track the friction of doing business across major markets.</p>", unsafe_allow_html=True)

try:
    df_tefi = pd.read_csv("data/tefi_raw.csv")
    
    # Premium Chart Styling - Clean & Minimal
    fig = px.bar(
        df_tefi.sort_values("TEFI Score (0-100)"), 
        x="Country", 
        y="TEFI Score (0-100)", 
        color="TEFI Score (0-100)",
        # Professional Monochromatic Blue Scale
        color_continuous_scale=["#CBD5E1", "#94A3B8", "#64748B", "#1E3A8A"],
    )
    
    fig.update_layout(
        height=450, 
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter", size=12, color="#475569"),
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Friction Score (Lower is Better)"),
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter")
    )
    # Remove plotly logo for cleaner look
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
except FileNotFoundError:
    st.error("TEFI Data not found. Please run data update.")

st.markdown("---")

# -----------------------------------------------------------------------------
# LATEST INSIGHTS (Grid Layout)
# -----------------------------------------------------------------------------
st.markdown("## Latest Insights")
st.write("Analysis of tax policy changes that impact NZ exporters.")

posts_dir = "posts"
if os.path.exists(posts_dir):
    files = sorted(os.listdir(posts_dir), reverse=True) 
    
    col1, col2 = st.columns(2)
    
    for i, filename in enumerate(files):
        if filename.endswith(".md"):
            with open(os.path.join(posts_dir, filename), "r") as f:
                content = f.read()
                
            # Parse Frontmatter
            metadata = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]
                    for line in frontmatter.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip().strip('"')
            else:
                body = content
                metadata["title"] = filename.replace(".md", "")
                metadata["date"] = ""
            
            # Display Card
            with (col1 if i % 2 == 0 else col2):
                with st.container():
                    st.markdown(f"#### {metadata.get('title', 'Untitled')}")
                    st.caption(f"PUBLISHED: {metadata.get('date', '').upper()}")
                    st.markdown(body[:180] + "...") 
                    st.button(f"Read Article", key=f"read_{i}")

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        <p><strong>ByteMind Ltd</strong></p>
        <p>Strategic Tax Intelligence & Economic Data Analytics</p>
        <p style="opacity: 0.6; font-size: 0.75rem; margin-top: 1rem;">© 2026 All Rights Reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)
