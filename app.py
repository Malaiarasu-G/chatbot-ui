import os
import requests
import streamlit as st
from databricks.sdk.core import Config

# ── Databricks auth (for app-to-app calls) ──────────────────────
_cfg = Config()

def _get_auth_headers():
    """Return headers with a valid Bearer token for the backend app."""
    return _cfg.authenticate()

# ── Backend API URL (chatbot-api endpoint) ───────────────────────
API_BASE_URL = os.getenv(
    "CHATBOT_API_URL",
    "https://chatbot-api-7474647357732356.aws.databricksapps.com",
)

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot", page_icon="\U0001f4ac", layout="centered")

# ── Custom CSS for chat styling ────────────────────────────────────
st.markdown(
    """
    <style>
    .stChatMessage { padding: 0.75rem 1rem; }
    .stApp header { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────
st.title("\U0001f4ac AI Chatbot")
st.caption(f"Powered by Azure OpenAI GPT-4o  |  Backend: `{API_BASE_URL}`")

# ── Sidebar controls ───────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 128, 4096, 1024, 128)
    system_prompt = st.text_area(
        "System prompt",
        value="You are a helpful AI assistant. Answer concisely and accurately.",
        height=100,
    )
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# ── Initialise chat history ───────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Display existing messages ─────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ─────────────────────────────────────────────────────
if prompt := st.chat_input("Type your message..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build payload with system prompt + history
    api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # Call the FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/api/chat",
                    json={
                        "messages": api_messages,
                        "stream": False,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    headers=_get_auth_headers(),
                    timeout=120,
                )
                resp.raise_for_status()
                assistant_text = resp.json()["content"]
            except requests.exceptions.ConnectionError:
                assistant_text = (
                    "Could not reach the backend. "
                    f"Make sure **chatbot-api** is running at `{API_BASE_URL}`."
                )
            except Exception as e:
                assistant_text = f"Error: {e}"

        st.markdown(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
