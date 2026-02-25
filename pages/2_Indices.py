import streamlit as st
import pandas as pd
import plotly.express as px
import utils

st.set_page_config(page_title="Indices | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS
utils.load_css()

st.title("ByteMind Economic Indices")
st.markdown("Real-time economic indicators powered by open data.")

# --- Methodology Expander ---
with st.expander("📊 View Methodology & Data Sources"):
    st.markdown("""
    ### 1. Tax Efficiency Friction Index (TEFI)
    **Objective:** Measures the friction businesses face due to corporate tax rates and compliance burden.
    
    **Formula:**
    $$
    \\text{TEFI Score} = \\text{Normalize} \\left( (\\text{Tax Rate} \\times 1.5) + \\frac{\\text{Compliance Hours}}{5} \\right)
    $$
    *Where 'Normalize' scales the raw friction score from 0 (Best) to 100 (Worst).*
    
    **Data Sources:**
    *   **Corporate Tax Rates:** [OECD Corporate Tax Statistics (CTS)](https://stats.oecd.org/Index.aspx?DataSetCode=CTS_CIT) - Table II.1.
    *   **Compliance Hours:** World Bank Doing Business (Historical) & PwC Paying Taxes Reports.
    
    ### 2. NZ SME Resilience Index
    **Objective:** Tracks the economic health of Small-to-Medium Enterprises in New Zealand using real-time spending and growth data.
    
    **Components:**
    *   **Retail Spending Trend (50% Weight):** Monthly change in Electronic Card Transactions (ECT) - Retail Industry (Seasonally Adjusted).
        *   *Source:* [Stats NZ Electronic Card Transactions](https://www.stats.govt.nz/information-releases/)
    *   **Enterprise Growth (30% Weight):** Year-on-Year growth in registered enterprises.
        *   *Source:* Stats NZ Business Demography Statistics.
    *   **Employment Growth (20% Weight):** Year-on-Year growth in SME employment.
        *   *Source:* Stats NZ Business Demography Statistics.
    """)

# Tabs for different indices
tab1, tab2 = st.tabs(["Tax Efficiency Friction Index (TEFI)", "NZ SME Resilience Index"])

# -----------------------------------------------------------------------------
# INDEX 1: TECH EXPORT FRICTION
# -----------------------------------------------------------------------------
st.markdown("### 1. Tech Export Friction Index (TEFI)")
st.write("**What is it?** A measure of how difficult and costly it is for a NZ tech company to expand into these markets.")
st.caption("Lower Score = Easier to do business. Higher Score = More tax/compliance friction.")

# Methodology Section
with st.expander("Methodology & Data Sources"):
    st.markdown(
        """
        ### Methodology
        The **Tech Export Friction Index (TEFI)** is a composite score (0-100) calculated using a weighted average of:
        1.  **Corporate Tax Rate (60%):** The statutory top corporate tax rate (including state/local taxes).
        2.  **Compliance Burden (40%):** Estimated hours per year to prepare and pay taxes.
        
        ### Data Sources (Verified 2026)
        *   **Corporate Tax Rates:** Sourced from the *OECD Corporate Tax Statistics 2025* and *Tax Foundation*.
        *   **Compliance Hours:** Sourced from *World Bank Doing Business* (Historical archives) and *PWC Paying Taxes* reports.
        
        *Note: This data is for informational purposes only. Always consult a tax professional.*
        """
    )

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
    
    st.caption(f"Last Data Update: {df['Last Updated'].iloc[0]}")
        
except FileNotFoundError:
    st.error("Data file 'data/tefi_raw.csv' not found. Please contact administrator.")

st.divider()

# -----------------------------------------------------------------------------
# INDEX 2: NZ SME RESILIENCE
# -----------------------------------------------------------------------------
st.markdown("### 2. NZ SME Resilience Index")
st.write("**What is it?** A real-time pulse of New Zealand's small business health, based on official Stats NZ data.")

# Load Real Data
try:
    df_sme = pd.read_csv("data/nz_sme_resilience.csv")
    
    # Calculate Score dynamically or read from attrs if possible (CSV doesn't store attrs, so we recalc or read)
    # Simple Recalc for display consistency
    # Weights: Spending (50%), Enterprise Growth (30%), Employment (20%)
    # Base 50
    spending = df_sme.loc[df_sme['Metric'].str.contains("Spending"), "Value (%)"].values[0]
    enterprise = df_sme.loc[df_sme['Metric'].str.contains("Enterprise"), "Value (%)"].values[0]
    employment = df_sme.loc[df_sme['Metric'].str.contains("Employment"), "Value (%)"].values[0]
    
    score = 50 + (spending * 10) + (enterprise * 5) + (employment * 2)
    score = round(score, 1)

    # Display Score
    col_score, col_desc = st.columns([1, 2])
    
    with col_score:
        st.metric(label="Current Resilience Score (0-100)", value=score, delta=f"{spending}% Spending Trend")
        
    with col_desc:
        if score > 55:
            st.success("The SME sector is showing strong growth signals.")
        elif score < 45:
            st.error("The SME sector is under significant pressure (Contraction).")
        else:
            st.warning("The SME sector is holding steady but facing headwinds.")
            
        st.markdown(
            """
            **Key Drivers:**
            *   **Retail Spending:** A proxy for consumer confidence.
            *   **Enterprise Counts:** Are businesses opening or closing?
            *   **Employment:** Is the labor market expanding?
            """
        )

    # Data Table
    st.markdown("#### Underlying Indicators (Stats NZ)")
    st.dataframe(df_sme, use_container_width=True)
    
    st.caption(f"Data Sources: {', '.join(df_sme['Source'].unique())}")

except FileNotFoundError:
    st.info("SME Index Data is being compiled. Please check back shortly.")
