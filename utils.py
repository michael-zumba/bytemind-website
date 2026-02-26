import streamlit as st
from PIL import Image
import os

def load_css(file_name="assets/style.css"):
    """
    Safely load CSS file. If file not found (e.g. during some deployment edge cases),
    it fails silently without crashing the app.
    """
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Fallback: Just don't apply styles
        pass

def sidebar_info():
    """
    Renders the consistent sidebar profile and contact info across all pages.
    """
    with st.sidebar:
        # Profile Image
        try:
            # Check if file exists to avoid ugly errors
            if os.path.exists("assets/images/profile_dr_zhang.png"):
                image = Image.open("assets/images/profile_dr_zhang.png")
                st.image(image, use_container_width=True)
        except Exception:
            pass

        # Profile Card HTML
        st.markdown(
            """
            <div class="profile-card">
                <div class="profile-name">Dr. Yuqian Zhang</div>
                <div class="profile-role">Founder & Principal</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Contact Links
        st.markdown("### Connect")
        st.markdown(
            """
            <a href="https://www.linkedin.com/in/yuqian-michael-zhang-744530142/" target="_blank" class="social-link">
                <span>LinkedIn Profile</span>
            </a>
            <a href="mailto:bytemind.nz@gmail.com" class="social-link">
                <span>Email Me</span>
            </a>
            """,
            unsafe_allow_html=True
        )
        
        st.write("")
        st.markdown("---")
        st.caption("© 2026 ByteMind Ltd.\nNew Zealand Tax Consultancy.")
