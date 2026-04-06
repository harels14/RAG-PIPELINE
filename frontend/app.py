import streamlit as st
import requests
import websocket
import json

API_URL = "https://rag-pipeline-production-b0b8.up.railway.app"
WS_URL = "wss://rag-pipeline-production-b0b8.up.railway.app/rag/ws"

st.set_page_config(page_title="Siemens AI Assistant", page_icon="🏢", layout="centered")

# --- Auth ---
params = st.query_params
user_id = params.get("user_id")

if not user_id:
    st.title("Siemens AI Assistant")
    st.subheader("Sign In")
    entered_id = st.text_input("Enter your User ID")
    if st.button("Sign In") and entered_id:
        st.query_params["user_id"] = entered_id
        st.rerun()
    st.divider()
    if st.button("New user — Create User ID"):
        resp = requests.post(f"{API_URL}/users/register")
        new_id = resp.json()["user_id"]
        st.query_params["user_id"] = new_id
        st.rerun()
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
    uploaded_file = st.file_uploader("Choose a file", type="pdf")
    if uploaded_file and st.button("Upload"):
        with st.spinner("Uploading..."):
            resp = requests.post(
                f"{API_URL}/documents/upload",
                data={"userid": user_id},
                files={"file": uploaded_file}
            )
        if resp.status_code == 200:
            st.success(f"Uploaded {resp.json()['stats']['chunks_created']} chunks")
        else:
            st.error("Upload failed")
    st.divider()
    st.subheader("Uploaded Files")
    files_resp = requests.get(f"{API_URL}/users/{user_id}/files")
    files = files_resp.json().get("files", []) if files_resp.status_code == 200 else []
    if files:
        for f in files:
            col1, col2 = st.columns([4, 1])
            col1.caption(f)
            if col2.button("🗑️", key=f):
                requests.delete(f"{API_URL}/users/{user_id}/files/{f}")
                st.rerun()
    else:
        st.caption("No files uploaded yet")
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- Chat ---
st.title("Siemens AI Assistant")

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

        ws.close()
        placeholder.markdown(full_response)
        if sources:
            st.caption("Sources: " + ", ".join(sources))

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources
    })
