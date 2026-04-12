import streamlit as st
import requests
import websocket
import json
from urllib.parse import quote

#streamlit url - https://rag-pipeline-harel.streamlit.app/?user_id=75f21fc3-9c71-441e-8ce0-1eb7d18cb335
API_URL = "https://rag-pipeline-production-b0b8.up.railway.app"
WS_URL = "wss://rag-pipeline-production-b0b8.up.railway.app/rag/ws"

st.set_page_config(page_title="Siemens AI Assistant", page_icon="🏢", layout="centered")

@st.cache_data(ttl=10)
def fetch_files(user_id):
    resp = requests.get(f"{API_URL}/users/{user_id}/files")
    return resp.json().get("files", []) if resp.status_code == 200 else []

# --- Auth ---
params = st.query_params
user_id = params.get("user_id")

if not user_id:
    st.title("Siemens AI Assistant")
    tab_login, tab_register = st.tabs(["Sign In", "Register"])

    with tab_login:
        login_id = st.text_input("User ID", key="login_id")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In"):
            resp = requests.post(f"{API_URL}/users/login", data={"user_id": login_id, "password": login_pass})
            if resp.status_code == 200:
                st.query_params["user_id"] = login_id
                st.rerun()
            else:
                st.error("Invalid user ID or password")

    with tab_register:
        reg_pass = st.text_input("Choose a password", type="password", key="reg_pass")
        reg_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2")
        if st.button("Create Account"):
            if reg_pass != reg_pass2:
                st.error("Passwords do not match")
            elif not reg_pass:
                st.error("Password cannot be empty")
            else:
                resp = requests.post(f"{API_URL}/users/register", data={"password": reg_pass})
                if resp.status_code == 200:
                    new_id = resp.json()["user_id"]
                    st.success(f"Your User ID: `{new_id}`")
                    st.info("Save this ID — you will need it to sign in next time")
                    st.query_params["user_id"] = new_id
                else:
                    st.error("Registration failed")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.image("https://1000logos.net/wp-content/uploads/2021/11/Siemens-logo.jpg", width=250)
    st.caption(f"User ID: `{user_id}`")
    if st.button("Sign Out"):
        st.query_params.clear()
        st.rerun()
    st.divider()
    st.subheader("Upload PDF")
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "pending_files" not in st.session_state:
        st.session_state.pending_files = []

    uploaded_files = st.file_uploader("Choose files", type="pdf", accept_multiple_files=True, key=st.session_state.uploader_key)

    if uploaded_files and st.button("Upload"):
        st.session_state.pending_files = [(f.name, f.read()) for f in uploaded_files]
        st.session_state.uploader_key += 1
        st.rerun()

    if st.session_state.pending_files:
        with st.spinner(f"Uploading {len(st.session_state.pending_files)} file(s) in parallel..."):
            resp = requests.post(
                f"{API_URL}/documents/upload-batch",
                data={"userid": user_id},
                files=[("files", (name, content, "application/pdf")) for name, content in st.session_state.pending_files]
            )
        if resp.status_code == 200:
            for r in resp.json()["results"]:
                st.success(f"{r['file']} — {r['chunks_created']} chunks")
            fetch_files.clear()
        else:
            st.error("Upload failed")
        st.session_state.pending_files = []

    st.divider()
    st.subheader("Uploaded Files")
    files = fetch_files(user_id)
    if files:
        for f in files:
            col1, col2 = st.columns([4, 1])
            col1.caption(f)
            if col2.button("🗑️", key=f):
                with st.spinner():
                    requests.delete(f"{API_URL}/users/{user_id}/files/{quote(f)}")
                fetch_files.clear()
                st.rerun()
        if st.button("🗑️ Delete All", use_container_width=True):
            with st.spinner():
                requests.delete(f"{API_URL}/users/{user_id}/files")
            fetch_files.clear()
            st.rerun()
    else:
        st.caption("No files uploaded yet")
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Chat ---
st.markdown("<h1 style='text-align: center;'>Siemens AI Assistant</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption("Sources: " + ", ".join(msg["sources"]))

if question := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        sources = []

        try:
            ws = websocket.WebSocket()
            ws.connect(WS_URL)
            ws.send(json.dumps({"userid": user_id, "question": question}))

            while True:
                msg = json.loads(ws.recv())
                if msg["type"] == "chunk":
                    full_response += msg["content"]
                    placeholder.markdown(full_response + "▌")
                elif msg["type"] == "sources":
                    sources = msg["content"]
                    break
                elif msg["type"] == "error":
                    placeholder.error(f"Server error: {msg['content']}")
                    break

            ws.close()
        except Exception as e:
            placeholder.error(f"Connection error: {e}")

        placeholder.markdown(full_response)
        if sources:
            st.caption("Sources: " + ", ".join(sources))

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources
    })
