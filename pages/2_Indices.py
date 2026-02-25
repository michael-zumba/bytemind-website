import streamlit as st
import pandas as pd
import plotly.express as px
import utils

st.set_page_config(page_title="Indices | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS
utils.load_css()

st.markdown("# ByteMind Indices")
st.write(
    """
    We construct rigorous economic indices to help businesses understand market conditions.
    This data drives our consulting advice.
    """
)

# -----------------------------------------------------------------------------
# INDEX 1: TECH EXPORT FRICTION
# -----------------------------------------------------------------------------
st.markdown("### 1. Tech Export Friction Index (TEFI)")
st.write("**What is it?** A measure of how difficult and costly it is for a NZ tech company to expand into these markets.")
st.caption("Lower Score = Easier to do business. Higher Score = More tax/compliance friction.")

# Load Real Data from CSV
try:
    df = pd.read_csv("data/tefi_raw.csv")
    
    # Interactive Chart
    fig = px.bar(
        df.sort_values("TEFI Score (0-100)"), 
        x="Country", 
        y="TEFI Score (0-100)", 
        color="TEFI Score (0-100)",
        color_continuous_scale=["#E2E8F0", "#3B82F6", "#1E40AF"], # Professional Blues
        text="TEFI Score (0-100)",
        title="TEFI 2026: Tax & Compliance Friction by Country"
    )
    fig.update_layout(
        xaxis_title="", 
        yaxis_title="Friction Score (Lower is Better)",
        plot_bgcolor="white",
        font=dict(family="Plus Jakarta Sans", size=12, color="#334155")
    )
    st.plotly_chart(fig, use_container_width=True)

    # Data Table
    with st.expander("View Underlying Data"):
        st.dataframe(df, use_container_width=True)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode('utf-8'),
            "tefi_data_2026.csv",
            "text/csv"
        )
        
except FileNotFoundError:
    st.error("Data file 'data/tefi_raw.csv' not found. Please contact administrator.")

st.divider()

# -----------------------------------------------------------------------------
# INDEX 2: COMING SOON
# -----------------------------------------------------------------------------
st.markdown("### 2. NZ SME Resilience Index")
st.info("Coming Q3 2026. This index will track the financial health of 500 NZ small businesses against inflation and tax changes.")
