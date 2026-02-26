import streamlit as st
import pandas as pd
import plotly.express as px
import utils

st.set_page_config(page_title="Indices | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

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

with tab1:
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
            paper_bgcolor="white",
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
        st.error("TEFI Data not found.")

with tab2:
    st.markdown("### 2. NZ SME Resilience Index")
    st.info("Fetching real-time data from Stats NZ...")
    # Add SME content here if data is available
    # For now, placeholder or check fetch_nz_data.py integration
    st.write("This index tracks the health of NZ SMEs using real-time spending data.")
    try:
        df_sme = pd.read_csv("data/nz_sme_resilience.csv")
        st.line_chart(df_sme.set_index("Date")["SME_Resilience_Score"])
    except:
        st.write("Data currently being compiled.")
