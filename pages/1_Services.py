import streamlit as st
import utils

st.set_page_config(page_title="Services | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

st.markdown(
    """
    <div class="animate-fade-in-up">
        <div class="badge">Expertise</div>
        <h1>Our Services</h1>
        <p style="font-size: 1.2rem; color: #64748B;">Specialized tax advice for New Zealand businesses looking to grow.</p>
    </div>
    """, 
    unsafe_allow_html=True
)
st.write("")

# -----------------------------------------------------------------------------
# SERVICE 1
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 1. The Global Growth Roadmap")
        st.markdown("**Best for:** <span style='color:#1E3A8A; font-weight:600'>Startups & Tech Exporters</span>", unsafe_allow_html=True)
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

st.write("")

# -----------------------------------------------------------------------------
# SERVICE 2
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 2. Fractional Tax Director")
        st.markdown("**Best for:** <span style='color:#1E3A8A; font-weight:600'>Scaling Companies ($5M+ Revenue)</span>", unsafe_allow_html=True)
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

st.write("")

# -----------------------------------------------------------------------------
# SERVICE 3
# -----------------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 3. SME Tax Health Check")
        st.markdown("**Best for:** <span style='color:#1E3A8A; font-weight:600'>Established NZ Businesses</span>", unsafe_allow_html=True)
        st.write(
            """
            A comprehensive review of your current tax setup to find savings and fix risks.
            
            *   **Structure Review:** Are you using the right Trusts or Companies?
            *   **Compliance Audit:** Are you meeting all IRD requirements?
            """
        )
    
    with col2:
        st.warning("Why do this? Most businesses overpay tax simply because they are structured incorrectly.")

st.markdown("---")
st.markdown("<h3 style='text-align: center;'>Ready to scale?</h3>", unsafe_allow_html=True)

col_c1, col_c2, col_c3 = st.columns([1, 0.6, 1])
with col_c2:
    if st.button("Start the Conversation", use_container_width=True):
        st.switch_page("pages/4_Contact.py")
