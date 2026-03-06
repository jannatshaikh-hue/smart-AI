import streamlit as st
from core.rag_engine import RAGEngine
import os

st.set_page_config(page_title="Smart AI Agent", layout="wide")

st.title("🤖 Smart AI Agent")

# -------------------------
# Load Tavily API Key
# -------------------------

if "tavily_api_key" not in st.session_state:
    try:
        st.session_state.tavily_api_key = st.secrets["TAVILY_API_KEY"]
    except:
        st.session_state.tavily_api_key = ""

# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("Settings")

api_key = st.sidebar.text_input(
    "Enter Tavily API Key",
    value=st.session_state.tavily_api_key,
    type="password"
)

if api_key:
    st.session_state.tavily_api_key = api_key

# -------------------------
# Check API Key
# -------------------------

if not st.session_state.tavily_api_key:
    st.warning("⚠️ Tavily not configured")
    st.stop()
else:
    st.success("✅ Tavily Connected")

# -------------------------
# Initialize RAG Engine
# -------------------------

rag = RAGEngine(api_key=st.session_state.tavily_api_key)

# -------------------------
# Chat Interface
# -------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask anything...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        response = rag.query(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------
# Display Chat
# -------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
