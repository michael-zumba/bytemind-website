import streamlit as st

st.set_page_config(page_title="About | ByteMind Ltd", page_icon="🧠", layout="wide")

import utils

# Custom CSS
utils.load_css()

st.title("About Us")

# -----------------------------------------------------------------------------
# FOUNDER PROFILE
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    # Placeholder for a photo
    st.image("https://placehold.co/400x400?text=Dr+Zhang", caption="Dr. Yuqian Zhang")

with col2:
    st.header("Dr. Yuqian Zhang")
    st.subheader("Founder & Principal Consultant")
    st.write(
        """
        Dr. Zhang is a **Lecturer in Taxation** based in New Zealand, combining deep academic research with practical business strategy.
        
        Unlike traditional accountants who focus on "what happened last year," Dr. Zhang focuses on **"what will happen next year."** 
        
        He specializes in helping businesses navigate complex tax environments, using rigorous data analysis to uncover opportunities that others miss.
        """
    )
    st.markdown(
        """
        *   **Expertise:** International Tax, SME Strategy, Economic Indices.
        *   **Philosophy:** "Tax is not just a cost; it's a variable you can manage."
        """
    )

st.divider()

# -----------------------------------------------------------------------------
# MISSION
# -----------------------------------------------------------------------------
st.header("Our Mission")
st.markdown(
    """
    To bridge the gap between **Academic Rigour** and **Business Reality**.
    
    We believe that small and medium businesses deserve the same level of sophisticated tax planning and data intelligence as large multinationals.
    """
)
