import streamlit as st

st.set_page_config(page_title="Services | ByteMind Ltd", page_icon="🧠", layout="wide")

import utils

# Custom CSS
utils.load_css()

st.title("Our Services")
st.write("We offer specialized tax advice for New Zealand businesses looking to grow.")

# -----------------------------------------------------------------------------
# SERVICE 1
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("1. The Global Growth Roadmap")
        st.markdown("**Best for: Startups & Tech Exporters**")
        st.write(
            """
            Expanding to the USA, UK, or Australia? We build you a custom tax plan so you don't get stuck with unexpected bills.
            
            *   **Entity Structure:** Should you open a subsidiary or a branch?
            *   **Transfer Pricing:** How to move money between countries legally.
            *   **Sales Tax Check:** Do you need to register for GST/VAT in other countries?
            """
        )
        st.caption("Starting from $5,000 + GST")

    with col2:
        st.info("Deliverable: A 10-page strategic report tailored to your expansion plan.")

st.divider()

# -----------------------------------------------------------------------------
# SERVICE 2
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("2. Fractional Tax Director")
        st.markdown("**Best for: Scaling Companies ($5M+ Revenue)**")
        st.write(
            """
            Too big for a general accountant, too small for a full-time Tax Manager? Hire us on a monthly retainer.
            
            *   **Quarterly Strategy Sessions:** We review your plans every 3 months.
            *   **Contract Review:** We check your big deals for tax risks.
            *   **Ad-hoc Support:** Call us when you have a tricky question.
            """
        )
        st.caption("Starting from $3,000 / month")

    with col2:
        st.success("Result: The peace of mind of a Big 4 partner, at a fraction of the cost.")

st.divider()

# -----------------------------------------------------------------------------
# SERVICE 3
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("3. SME Tax Health Check")
        st.markdown("**Best for: Established NZ Businesses**")
        st.write(
            """
            A comprehensive review of your current tax setup to find savings and fix risks.
            
            *   **Structure Review:** Are you using the right Trusts or Companies?
            *   **Compliance Audit:** Are you meeting all IRD requirements?
            """
        )
    
    with col2:
        st.warning("Why do this? Most businesses overpay tax simply because they are structured incorrectly.")

st.write("")
st.write("")
if st.button("Discuss Your Needs"):
    st.switch_page("pages/4_Contact.py")
