import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ByteMind Ltd | Strategic Tax Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

import utils

# Load Custom CSS
utils.load_css()

# -----------------------------------------------------------------------------
# HERO SECTION
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.title("Smarter Tax Strategy for Global Growth.")
    st.markdown(
        """
        ### **We turn complex data into simple, actionable tax plans.**
        
        Expanding your business overseas? Don't let tax compliance eat your profits.
        ByteMind combines **academic rigour** with **practical consulting** to help New Zealand SMEs and Tech Exporters grow safely.
        """
    )
    st.write("")
    if st.button("See How We Help"):
        st.switch_page("pages/1_Services.py")

with col2:
    # A placeholder chart to demonstrate "Data Intelligence" immediately
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
        color_continuous_scale="Blues"
    )
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# VALUE PROPOSITION (Why Us?)
# -----------------------------------------------------------------------------
st.subheader("Why ByteMind?")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### 📊 Data-Driven")
    st.write("We don't guess. We use proprietary economic indices to benchmark your tax efficiency against the market.")

with c2:
    st.markdown("#### 🎓 Expert Led")
    st.write("Led by Dr. Yuqian Zhang, a taxation academic and industry expert. You get university-level insight applied to business problems.")

with c3:
    st.markdown("#### 🌏 Export Focused")
    st.write("Specialists in helping NZ companies navigate the tax maze of the USA, UK, and Australia.")

st.divider()

# -----------------------------------------------------------------------------
# LATEST INSIGHTS
# -----------------------------------------------------------------------------
st.subheader("Latest Insights")
st.info("💡 **Did you know?** The UK recently changed its R&D tax credit rules, which may impact NZ SaaS companies with London offices.")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**The Hidden Cost of US Sales Tax**")
    st.caption("Feb 2026 • 3 min read")
    st.write("Selling software to US customers? You might have a tax liability even without an office there.")
with col_b:
    st.markdown("**Structuring for Exit**")
    st.caption("Jan 2026 • 4 min read")
    st.write("How to set up your company today to maximize your payout when you sell in 5 years.")

st.write("")
st.markdown("---")
st.markdown("© 2026 ByteMind Ltd. All Rights Reserved.")
