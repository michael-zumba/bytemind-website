import streamlit as st
import pandas as pd
import plotly.express as px
import utils

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ByteMind Ltd | Strategic Tax Intelligence",
    page_icon="assets/images/profile_dr_zhang.png", # Use profile pic as favicon if possible, or fallback to None
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Custom CSS
utils.load_css()

# -----------------------------------------------------------------------------
# HERO SECTION
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown('<div class="hero-title">Smarter Tax Strategy for Global Growth.</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-subtitle">
        Expanding your business overseas? Don't let tax compliance eat your profits. 
        ByteMind combines <strong>academic rigour</strong> with <strong>practical consulting</strong> to help New Zealand SMEs and Tech Exporters grow safely.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")
    
    # Primary CTA
    if st.button("Explore Services"):
        st.switch_page("pages/1_Services.py")

with col2:
    # A cleaner, more professional chart
    df_mock = pd.DataFrame({
        "Country": ["USA", "Australia", "UK", "Canada", "Singapore"],
        "Complexity Score": [85, 60, 55, 50, 40],
        "Profit Impact": [12, 8, 7, 6, 4]
    })
    fig = px.bar(
        df_mock, 
        x="Country", 
        y="Complexity Score", 
        color="Complexity Score",
        title="Tech Export Friction Index (Preview)",
        color_continuous_scale=["#E2E8F0", "#3B82F6", "#1E40AF"], # Professional Blues
    )
    fig.update_layout(
        height=400, 
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="white",
        font=dict(family="Plus Jakarta Sans", size=12, color="#334155")
    )
    fig.update_traces(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.write("")
st.write("")

# -----------------------------------------------------------------------------
# VALUE PROPOSITION (Why Us?)
# -----------------------------------------------------------------------------
st.markdown("## Why ByteMind?")

c1, c2, c3 = st.columns(3)

with c1:
    with st.container():
        st.markdown("### Data-Driven")
        st.write("We don't guess. We use proprietary economic indices to benchmark your tax efficiency against the market.")

with c2:
    with st.container():
        st.markdown("### Expert Led")
        st.write("Led by Dr. Yuqian Zhang, a taxation academic and industry expert. You get university-level insight applied to business problems.")

with c3:
    with st.container():
        st.markdown("### Export Focused")
        st.write("Specialists in helping NZ companies navigate the tax maze of the USA, UK, and Australia.")

st.write("")
st.write("")

# -----------------------------------------------------------------------------
# LATEST INSIGHTS
# -----------------------------------------------------------------------------
st.markdown("## Latest Insights")
st.info("The UK recently changed its R&D tax credit rules, which may impact NZ SaaS companies with London offices.")

col_a, col_b = st.columns(2)
with col_a:
    with st.container():
        st.markdown("### The Hidden Cost of US Sales Tax")
        st.caption("Feb 2026 • 3 min read")
        st.write("Selling software to US customers? You might have a tax liability even without an office there.")
with col_b:
    with st.container():
        st.markdown("### Structuring for Exit")
        st.caption("Jan 2026 • 4 min read")
        st.write("How to set up your company today to maximize your payout when you sell in 5 years.")

st.markdown("---")
st.caption("© 2026 ByteMind Ltd. All Rights Reserved.")
