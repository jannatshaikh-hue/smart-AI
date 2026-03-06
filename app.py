import streamlit as st
import tempfile
from pathlib import Path
import os
import sys
import time
from datetime import datetime

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Smart AI Agent",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'tavily_api_key' not in st.session_state:
    st.session_state.tavily_api_key = ""
if 'web_agent' not in st.session_state:
    st.session_state.web_agent = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Create folders
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/vector_store", exist_ok=True)

# ============================================================
# IMPORT CORE MODULES
# ============================================================
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import document processor and RAG engine
    try:
        from core.document_processor import DocumentProcessor
        from core.rag_engine import EnhancedRAGEngine
        doc_processor_available = True
    except ImportError as e:
        print(f"Document processor import error: {e}")
        doc_processor_available = False
        doc_processor = None
        rag_engine = None
    
    # Import web search agent
    try:
        from core.web_search import WebSearchAgent
        web_search_available = True
    except ImportError as e:
        print(f"Web search import error: {e}")
        web_search_available = False
    
    class Config:
        DATA_DIR = "./data"
        UPLOAD_DIR = "./data/uploads"
        VECTOR_STORE_DIR = "./data/vector_store"
        DB_PATH = "./data/user_progress.db"
    
    config = Config()
    
    # Initialize document processor if available
    if doc_processor_available:
        doc_processor = DocumentProcessor(config)
        rag_engine = EnhancedRAGEngine(config)
    
    # Initialize web agent if API key exists
    if st.session_state.tavily_api_key and web_search_available:
        st.session_state.web_agent = WebSearchAgent(tavily_api_key=st.session_state.tavily_api_key)
    
    core_loaded = True
except Exception as e:
    st.error(f"Error loading modules: {e}")
    core_loaded = False
    doc_processor = None
    rag_engine = None

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("🤖 Smart AI Agent")
    st.markdown("---")
    
    # Mode Selection
    st.header("🎯 Mode")
    mode = st.radio(
        "Select mode:",
        ["💬 Smart Chat (Web Search)", "📄 Document Chat", "⚙️ Settings", "📊 Debug Info"],
        index=0
    )
    
    st.markdown("---")
    
    # Settings mode
    if mode == "⚙️ Settings":
        st.header("🔑 Tavily API Configuration")
        st.markdown("Get your free API key from [Tavily](https://tavily.com)")
        st.info("💡 1,000 free searches per month")
        
        with st.form("tavily_form"):
            tavily_key = st.text_input(
                "Tavily API Key", 
                type="password",
                value=st.session_state.tavily_api_key,
                help="Enter your Tavily API key"
            )
            
            submitted = st.form_submit_button("💾 Save Key", type="primary", use_container_width=True)
            if submitted:
                st.session_state.tavily_api_key = tavily_key
                # Reinitialize web agent
                if web_search_available and tavily_key:
                    st.session_state.web_agent = WebSearchAgent(tavily_api_key=tavily_key)
                st.success("✅ Tavily key saved!")
        
        # Test connection
        if st.button("🔍 Test Tavily Connection", use_container_width=True):
            if st.session_state.tavily_api_key:
                with st.spinner("Testing connection..."):
                    try:
                        test_agent = WebSearchAgent(tavily_api_key=st.session_state.tavily_api_key)
                        results = test_agent.search_web("test", num_results=1)
                        if results and results[0]['source'] == 'tavily':
                            st.success("✅ Connection successful! Your API key works.")
                        else:
                            st.error("❌ Connection failed. Check your key.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter an API key first")
    
    # Debug Info mode
    elif mode == "📊 Debug Info":
        st.header("🔍 Search History")
        if st.session_state.search_history:
            for record in st.session_state.search_history[-10:]:  # Last 10 searches
                if record.get('success', False):
                    st.success(f"✅ {record.get('query', '')[:30]}... ({record.get('result_count', 0)} results)")
                else:
                    st.error(f"❌ {record.get('query', '')[:30]}... - {record.get('error', 'Unknown error')}")
        else:
            st.info("No search history yet")
        
        # System info
        st.markdown("---")
        st.header("ℹ️ System Info")
        st.write(f"Tavily API Key: {'✅ Configured' if st.session_state.tavily_api_key else '❌ Not configured'}")
        st.write(f"Web Search Available: {'✅ Yes' if web_search_available else '❌ No'}")
        st.write(f"Documents Loaded: {len(st.session_state.documents)}")
        st.write(f"Chat Messages: {len(st.session_state.messages)}")
        
        if st.button("Clear History", use_container_width=True):
            st.session_state.search_history = []
            st.rerun()
    
    # Document Chat mode
    elif mode == "📄 Document Chat":
        st.header("📄 Upload Files")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['txt', 'pdf', 'docx', 'md'],
            accept_multiple_files=True,
            key="doc_uploader"
        )
        
        if uploaded_files:
            st.info(f"📋 {len(uploaded_files)} file(s) selected")
            
            if st.button("🚀 Process Files", type="primary", use_container_width=True):
                with st.spinner("Processing files..."):
                    new_documents = []
                    for uploaded_file in uploaded_files:
                        if uploaded_file.name not in st.session_state.uploaded_files:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                            
                            if doc_processor_available and doc_processor:
                                try:
                                    doc = doc_processor.process_file(tmp_path)
                                    doc['filename'] = uploaded_file.name
                                    new_documents.append(doc)
                                    st.session_state.uploaded_files.append(uploaded_file.name)
                                except Exception as e:
                                    st.error(f"Error processing {uploaded_file.name}: {e}")
                            
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                    
                    if new_documents:
                        st.session_state.documents.extend(new_documents)
                        if rag_engine:
                            rag_engine.add_documents(new_documents)
                        st.success(f"✅ Processed {len(new_documents)} file(s)!")
        
        if st.session_state.documents:
            st.markdown("---")
            st.header("📚 Your Documents")
            for i, doc in enumerate(st.session_state.documents):
                st.caption(f"📄 {i+1}. {doc.get('filename', 'Unknown')}")
            
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.documents = []
                st.session_state.uploaded_files = []
                st.rerun()
    
    # Smart Chat mode
    else:
        if st.session_state.tavily_api_key:
            st.success("🌐 Tavily Web Search is ACTIVE")
            st.caption(f"API Key: {st.session_state.tavily_api_key[:10]}...")
        else:
            st.warning("⚠️ Tavily not configured")
            st.info("Go to Settings to add your API key")
            st.markdown("[Get Free Key](https://tavily.com)")
        
        st.markdown("**Try asking:**")
        examples = [
            "What is quantum entanglement?",
            "Latest news about AI",
            "Explain black holes",
            "Mars exploration 2025",
            "Who is the current US President?",
            "Weather in London today"
        ]
        for ex in examples[:3]:
            if st.button(ex, use_container_width=True):
                st.session_state.example_question = ex
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

# Title based on mode
if mode == "💬 Smart Chat (Web Search)":
    st.title("🌐 Smart AI Agent - Real-Time Web Search")
    if st.session_state.tavily_api_key:
        st.caption("✅ Tavily web search active - getting real-time answers")
    else:
        st.caption("🔧 Tavily not configured - using knowledge base")
elif mode == "📄 Document Chat":
    st.title("📄 Document Q&A")
    if st.session_state.documents:
        st.caption(f"📚 {len(st.session_state.documents)} document(s) loaded")
    else:
        st.caption("📤 Upload documents in the sidebar")
elif mode == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.caption("Configure your Tavily API key")
else:
    st.title("📊 Debug Information")
    st.caption("Search history and diagnostics")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    if isinstance(source, dict):
                        title = source.get('title', 'Source')
                        link = source.get('link', '#')
                        snippet = source.get('snippet', '')
                        st.markdown(f"**[{title}]({link})**")
                        if snippet:
                            st.caption(snippet[:200] + "..." if len(snippet) > 200 else snippet)

# Chat input
prompt = st.chat_input("Type your question here...")

# Use example if clicked
if hasattr(st.session_state, 'example_question') and st.session_state.example_question:
    prompt = st.session_state.example_question
    st.session_state.example_question = None

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🌐 Searching the web in real-time..." if mode == "💬 Smart Chat (Web Search)" else "🔍 Processing..."):
            time.sleep(0.5)
            
            if mode == "💬 Smart Chat (Web Search)":
                # Smart web search mode with Tavily
                if st.session_state.tavily_api_key and st.session_state.web_agent:
                    try:
                        # Get answer from web agent
                        result = st.session_state.web_agent.answer_question(prompt)
                        response = result['answer']
                        sources = result.get('sources', [])
                        
                        # Add to search history
                        st.session_state.search_history.append({
                            'query': prompt,
                            'success': True,
                            'result_count': len(sources),
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception as e:
                        response = f"⚠️ Search error: {str(e)}"
                        sources = []
                        st.session_state.search_history.append({
                            'query': prompt,
                            'success': False,
                            'error': str(e),
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                else:
                    # No API key - use knowledge base
                    if st.session_state.web_agent:
                        response = st.session_state.web_agent.answer_question(prompt)['answer']
                    else:
                        response = f"""**About your question: "{prompt}"**

🔧 **Tavily API Key Required**

To enable real-time web search:
1. Sign up at [Tavily](https://tavily.com) (free)
2. Get your API key
3. Go to **Settings** in the sidebar
4. Enter your key and save

✨ **Benefits of Tavily:**
- 1,000 free searches per month
- Designed specifically for AI agents
- Real-time web search
- Accurate, relevant results

📚 **Until then, you can:**
- Ask about predefined topics (time, gravity, quantum physics)
- Upload documents in Document Chat mode
"""
                    sources = []
                
                st.markdown(response)
                
                # Show sources
                if sources and len(sources) > 0:
                    with st.expander("📚 Sources"):
                        for source in sources:
                            if isinstance(source, dict):
                                title = source.get('title', 'Source')
                                link = source.get('link', '#')
                                snippet = source.get('snippet', '')
                                st.markdown(f"**[{title}]({link})**")
                                if snippet:
                                    st.caption(snippet[:200] + "..." if len(snippet) > 200 else snippet)
                
            elif mode == "📄 Document Chat":
                # Document chat mode
                if st.session_state.documents and rag_engine:
                    contexts = [doc.get('text', '')[:500] for doc in st.session_state.documents]
                    response = rag_engine.generate_response(prompt, contexts)
                    sources = [{'title': doc.get('filename', 'Unknown'), 'link': '#', 'snippet': ''} for doc in st.session_state.documents[:3]]
                    st.markdown(response)
                else:
                    response = "📁 **No documents uploaded.** Please upload files first or switch to Smart Chat mode."
                    sources = []
                    st.markdown(response)
                    if not st.session_state.documents:
                        st.info("Go to Document Chat mode in the sidebar to upload files.")
            
            else:
                # Settings or Debug mode - shouldn't get here
                response = "Select a mode from the sidebar to start."
                sources = []
                st.markdown(response)
    
    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "sources": sources if 'sources' in locals() else []
    })

# Footer
st.markdown("---")
st.caption("🤖 Smart AI Agent - Powered by Tavily API | 1,000 free searches/month")