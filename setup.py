import streamlit as st

def configure_page():
    st.set_page_config(page_title="Newsletter PDF Builder", layout="wide")
    st.title("📬 Newsletter PDF Builder")

def authenticate():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        user_pw = st.text_input("🔒 Enter password to unlock preview tools", type="password")
        if user_pw == st.secrets["auth"]["password"]:
            st.success("🔓 Access granted.")
            st.session_state.authenticated = True
            st.rerun()
        elif user_pw:
            st.error("❌ Incorrect password.")
        st.stop()
