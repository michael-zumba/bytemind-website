import streamlit as st
import utils
from PIL import Image

st.set_page_config(page_title="About | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

st.markdown("# About Us")

# -----------------------------------------------------------------------------
# FOUNDER PROFILE
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 2.5])

with col1:
    try:
        image = Image.open("assets/images/profile_dr_zhang.png")
        st.image(image, caption="Dr. Yuqian Zhang", use_container_width=True)
    except FileNotFoundError:
        st.error("Profile image not found.")

with col2:
    st.markdown("## Dr. Yuqian Zhang")
    st.markdown("### Founder & Principal Consultant")
    st.write(
        """
        Dr. Zhang is a **Lecturer in Taxation** based in New Zealand, combining deep academic research with practical business strategy.
        
        Unlike traditional accountants who focus on "what happened last year," Dr. Zhang focuses on **"what will happen next year."** 
        
        He specializes in helping businesses navigate complex tax environments, using rigorous data analysis to uncover opportunities that others miss.
        """
    )
    st.info(
        """
        *   **Expertise:** International Tax, SME Strategy, Economic Indices.
        *   **Philosophy:** "Tax is not just a cost; it's a variable you can manage."
        """
    )

st.divider()

# -----------------------------------------------------------------------------
# MISSION
# -----------------------------------------------------------------------------
st.markdown("## Our Mission")
st.markdown(
    """
    To bridge the gap between **Academic Rigour** and **Business Reality**.
    
    We believe that small and medium businesses deserve the same level of sophisticated tax planning and data intelligence as large multinationals.
    """
)
