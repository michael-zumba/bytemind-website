import streamlit as st
import utils

st.set_page_config(page_title="Contact | ByteMind Ltd", page_icon="assets/images/profile_dr_zhang.png", layout="wide")

# Custom CSS & Sidebar
utils.load_css()
utils.sidebar_info()

st.markdown("# Get in Touch")
st.write("Ready to optimize your tax strategy? Let's talk.")

# -----------------------------------------------------------------------------
# CONTACT INFO
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Contact Details")
    st.markdown("**Email:** bytemind.nz@gmail.com")
    st.markdown("**Location:** New Zealand (Available Nationwide)")
    st.markdown("**LinkedIn:** [Dr Yuqian Michael Zhang](https://www.linkedin.com/in/yuqian-michael-zhang-744530142/)")
    
    st.success("We typically reply within 24 hours.")

# -----------------------------------------------------------------------------
# CONTACT FORM (Simple)
# -----------------------------------------------------------------------------
with col2:
    st.markdown("### Send us a message")
    with st.form("contact_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        topic = st.selectbox(
            "What do you need help with?",
            ["Global Growth Roadmap", "Tax Strategy Retainer", "General Inquiry"]
        )
        message = st.text_area("Message")
        
        submitted = st.form_submit_button("Send Message")
        
        if submitted:
            st.success(f"Thanks {name}! We'll be in touch about {topic} soon.")
