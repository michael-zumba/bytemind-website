import streamlit as st

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
