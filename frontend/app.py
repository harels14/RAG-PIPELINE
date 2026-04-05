import streamlit as st
import time

st.set_page_config(page_title="Siemens AI Assistant", page_icon="🏢", layout="centered")

st.title("Siemens Innovation Assitant")




with st.sidebar:
    st.image("https://1000logos.net/wp-content/uploads/2021/11/Siemens-logo.jpg", width=250) # רק כדוגמה
    st.header("Settings")
    st.info("System: RAG enabled")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()