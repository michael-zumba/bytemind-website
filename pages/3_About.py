import streamlit as st
import utils
from PIL import Image
import os

st.set_page_config(page_title="About | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

# -----------------------------------------------------------------------------
# FOUNDER PROFILE
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="animate-fade-in-up">
        <div class="badge">Our Expertise</div>
        <h1>Meet the Principal</h1>
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2 = st.columns([1.2, 2])

with col1:
    try:
        # Check for profile image
        if os.path.exists("assets/images/profile_dr_zhang.png"):
            image = Image.open("assets/images/profile_dr_zhang.png")
            st.image(image, caption="Dr. Yuqian Michael Zhang", use_container_width=True)
        else:
            st.warning("Profile image placeholder")
            
        # Authority Badges (Simulated)
        st.markdown(
            """
            <div style="margin-top: 1.5rem; text-align: center;">
                <span class="badge" style="background: white; border: 1px solid #E2E8F0; color: #475569;">PhD in Taxation</span>
                <span class="badge" style="background: white; border: 1px solid #E2E8F0; color: #475569;">University Lecturer</span>
                <span class="badge" style="background: white; border: 1px solid #E2E8F0; color: #475569;">CPA Australia</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Error loading profile: {e}")

with col2:
    st.markdown("## Dr. Yuqian Michael Zhang")
    st.markdown("### Founder & Principal Consultant")
    
    st.write(
        """
        Dr. Zhang is a **Senior Lecturer in Accounting** and **CPA** based in New Zealand, standing at the intersection of **academic rigour** and **practical business strategy**.
        
        With over 7 years of experience in advanced accounting research, Dr. Zhang specializes in **digital transformation**, **ESG disclosure**, and **cross-cultural financial reporting**. He doesn't just "do tax returns"—he leverages data analytics and textual analysis to design strategies that fuel sustainable growth.
        """
    )
    
    st.markdown(
        """
        > *"Most accountants focus on what happened last year. I focus on **what will happen next year**, and how we can position your business to take advantage of it."*
        """
    )
    
    st.write("")
    
    # Expertise Grid
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Academic Authority")
        st.caption("Senior Lecturer at Lincoln University. Published researcher in top-tier Q1 journals (ABDC-A).")
    with c2:
        st.markdown("#### Global Perspective")
        st.caption("Specialist in cross-border expansion, international financial reporting, and digital asset valuation.")

st.divider()

# -----------------------------------------------------------------------------
# THOUGHT LEADERSHIP (LinkedIn Embeds)
# -----------------------------------------------------------------------------
st.markdown("## Thought Leadership & Media")
st.write("Dr. Zhang regularly shares insights on LinkedIn, discussing the latest tax changes and economic trends.")

# Using Streamlit columns to create a grid of embedded content
l_col1, l_col2 = st.columns(2)

with l_col1:
    st.markdown("### Recent Analysis")
    st.info("Follow Dr. Zhang on LinkedIn for daily updates on NZ tax policy.")
    
    st.markdown(
        """
        <div style="border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; background: white;">
            <h4>Video Analysis: NZ Budget 2026</h4>
            <p>Dr. Zhang breaks down the implications of the latest budget for small business owners.</p>
            <a href="https://www.linkedin.com/in/yuqian-michael-zhang-744530142/recent-activity/all/" target="_blank">
                <button style="background-color: #0A66C2; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    Watch on LinkedIn
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

with l_col2:
    st.markdown("### Featured Content")
    st.markdown(
        """
        <div style="border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; background: white;">
            <h4>Trend Report: SME Resilience</h4>
            <p>Discussion on how rising compliance costs are affecting the 'SME engine' of the economy.</p>
            <a href="https://www.linkedin.com/in/yuqian-michael-zhang-744530142/recent-activity/all/" target="_blank">
                <button style="background-color: #0A66C2; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                    View Activity
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# -----------------------------------------------------------------------------
# MISSION
# -----------------------------------------------------------------------------
st.markdown("## Our Mission")
st.markdown(
    """
    To bridge the gap between **Academic Rigour** and **Business Reality**.
    
    We believe that small and medium businesses deserve the same level of sophisticated tax planning and data intelligence as large multinationals. By leveraging real-time data indices (like our TEFI and SME Resilience Index), we bring Big 4 quality insights to the engine room of the New Zealand economy.
    """
)
