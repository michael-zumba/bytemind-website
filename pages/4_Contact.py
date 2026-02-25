import streamlit as st

st.set_page_config(page_title="Contact | ByteMind Ltd", page_icon="🧠", layout="wide")

import utils

# Custom CSS
utils.load_css()

st.title("Get in Touch")
st.write("Ready to optimize your tax strategy? Let's talk.")

# -----------------------------------------------------------------------------
# CONTACT INFO
# -----------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Contact Details")
    st.markdown("📧 **Email:** contact@bytemind.co.nz")
    st.markdown("📍 **Location:** New Zealand (Available Nationwide)")
    st.markdown("💼 **LinkedIn:** [Dr Yuqian Zhang](#)")
    
    st.info("We typically reply within 24 hours.")

# -----------------------------------------------------------------------------
# CONTACT FORM (Simple)
# -----------------------------------------------------------------------------
with col2:
    st.subheader("Send us a message")
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
            # In a real app, this would send an email via API (e.g. SendGrid)
