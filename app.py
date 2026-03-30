import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load .env file first before anything else
load_dotenv()

from core.ingestor import ingest_pdf
from core.qa_engine import ask_question
from core.extractor import extract_key_info
from core.detector import detect_domain

st.set_page_config(page_title="DocuSense", page_icon="📄", layout="wide")

st.title("📄 DocuSense — Universal Document Intelligence")
st.caption("Upload any PDF. Ask questions. Get plain English answers.")

# ── Sidebar: upload + domain ──────────────────────────────────────────────────
with st.sidebar:
    st.header("1. Upload Your Document")
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    st.header("2. Domain (auto-detected)")
    domain_choice = st.selectbox(
        "Override if needed",
        ["Auto Detect", "Financial", "Construction", "Real Estate", "Investment", "Legal", "General"],
    )

    if uploaded_file:
        st.success(f"Loaded: {uploaded_file.name}")

# ── Main area ─────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.info("👈 Upload a PDF from the sidebar to get started.")
    st.stop()

# Save upload to temp location
pdf_path = Path("data/uploads") / uploaded_file.name
pdf_path.parent.mkdir(parents=True, exist_ok=True)
pdf_path.write_bytes(uploaded_file.read())

# Ingest once per file (cache by filename)
with st.spinner("Reading and indexing your document..."):
    vectorstore, image_count, text_chunks = ingest_pdf(str(pdf_path))

# Show summary of what was indexed
col1, col2 = st.columns(2)
col1.metric("📝 Text Chunks Indexed", text_chunks)
col2.metric("🖼️ Images Described & Indexed", image_count)

# Auto detect domain
if domain_choice == "Auto Detect":
    domain = detect_domain(str(pdf_path))
    st.sidebar.info(f"Detected domain: **{domain}**")
else:
    domain = domain_choice

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Key Insights (Auto Extract)", "💬 Ask Anything"])

# Tab 1 — Auto extraction
with tab1:
    st.subheader("Key Information Extracted")
    st.caption("Automatically pulled from your document — explained in plain English.")

    if st.button("Extract Key Insights", type="primary"):
        with st.spinner("Extracting and simplifying..."):
            results = extract_key_info(vectorstore, domain)
        for section, content in results.items():
            with st.expander(f"📌 {section}", expanded=True):
                st.write(content)

# Tab 2 — Free Q&A
with tab2:
    st.subheader("Ask Anything About Your Document")
    st.caption("Ask in plain English — no legal or technical knowledge needed.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_q = st.chat_input("e.g. What happens if the contractor misses the deadline?")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.write(user_q)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_question(vectorstore, user_q, st.session_state.chat_history)
            st.write(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})