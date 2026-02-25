import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Indices | ByteMind Ltd", page_icon="🧠", layout="wide")

import utils

# Custom CSS
utils.load_css()

st.title("ByteMind Indices")
st.write(
    """
    We construct rigorous economic indices to help businesses understand market conditions.
    This data drives our consulting advice.
    """
)

# -----------------------------------------------------------------------------
# INDEX 1: TECH EXPORT FRICTION
# -----------------------------------------------------------------------------
st.subheader("1. Tech Export Friction Index (TEFI)")
st.markdown("**What is it?** A measure of how difficult and costly it is for a NZ tech company to expand into these markets.")
st.caption("Lower Score = Easier to do business. Higher Score = More tax/compliance friction.")

# Dummy Data for Visualization
data = {
    "Country": ["USA", "Australia", "United Kingdom", "Singapore", "Canada", "Germany", "Japan"],
    "Corporate Tax Rate": [21, 30, 25, 17, 26.5, 30, 30.6],
    "Compliance Hours": [175, 150, 110, 80, 130, 218, 190],
    "TEFI Score (0-100)": [78, 65, 58, 35, 52, 82, 75]
}
df = pd.DataFrame(data)

# Interactive Chart
fig = px.bar(
    df.sort_values("TEFI Score (0-100)"), 
    x="Country", 
    y="TEFI Score (0-100)", 
    color="TEFI Score (0-100)",
    color_continuous_scale="Reds",
    text="TEFI Score (0-100)",
    title="TEFI 2026: Tax & Compliance Friction by Country"
)
fig.update_layout(xaxis_title="", yaxis_title="Friction Score (Lower is Better)")
st.plotly_chart(fig, use_container_width=True)

# Data Table
with st.expander("View Underlying Data"):
    st.dataframe(df)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode('utf-8'),
        "tefi_data_2026.csv",
        "text/csv"
    )

st.divider()

# -----------------------------------------------------------------------------
# INDEX 2: COMING SOON
# -----------------------------------------------------------------------------
st.subheader("2. NZ SME Resilience Index")
st.info("Coming Q3 2026. This index will track the financial health of 500 NZ small businesses against inflation and tax changes.")
