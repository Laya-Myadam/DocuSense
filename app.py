import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from core.ingestor import ingest_pdf
from core.qa_engine import ask_question, reset_memory
from core.extractor import extract_key_info
from core.detector import detect_domain
from core.exporter import export_to_pdf
from core.comparator import compare_documents

st.set_page_config(page_title="DocuSense", page_icon="📄", layout="wide")
st.title("📄 DocuSense — Universal Document Intelligence")
st.caption("Upload any PDF. Ask questions. Get plain English answers.")

# ── Session state init ────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "insights" not in st.session_state:
    st.session_state.insights = {}
if "vectorstore_b" not in st.session_state:
    st.session_state.vectorstore_b = None
if "filename_b" not in st.session_state:
    st.session_state.filename_b = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Primary PDF", type=["pdf"])

    st.header("2. Domain")
    domain_choice = st.selectbox(
        "Override if needed",
        ["Auto Detect", "Financial", "Construction", "Real Estate", "Investment", "Legal", "General"],
    )

    st.divider()
    st.header("3. Compare (optional)")
    uploaded_file_b = st.file_uploader("Second PDF for comparison", type=["pdf"])

    if uploaded_file:
        st.success(f"Doc A: {uploaded_file.name}")
    if uploaded_file_b:
        st.success(f"Doc B: {uploaded_file_b.name}")

# ── Guard ─────────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.info("👈 Upload a PDF from the sidebar to get started.")
    st.stop()

# ── Ingest primary doc ────────────────────────────────────────────────────────
pdf_path = Path("data/uploads") / uploaded_file.name
pdf_path.parent.mkdir(parents=True, exist_ok=True)
pdf_path.write_bytes(uploaded_file.getbuffer())

with st.spinner("Reading and indexing your document..."):
    vectorstore, image_count, text_chunks = ingest_pdf(str(pdf_path))

col1, col2 = st.columns(2)
col1.metric("📝 Text Chunks Indexed", text_chunks)
col2.metric("🖼️ Images Described & Indexed", image_count)

# Domain detection
if domain_choice == "Auto Detect":
    with st.spinner("Detecting document domain..."):
        domain = detect_domain(str(pdf_path))
    st.sidebar.info(f"Detected: **{domain}**")
else:
    domain = domain_choice

# Ingest second doc if uploaded
if uploaded_file_b:
    pdf_path_b = Path("data/uploads") / uploaded_file_b.name
    pdf_path_b.write_bytes(uploaded_file_b.getbuffer())
    with st.spinner("Indexing second document..."):
        vectorstore_b, _, _ = ingest_pdf(str(pdf_path_b))
    st.session_state.vectorstore_b = vectorstore_b
    st.session_state.filename_b = uploaded_file_b.name

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = ["🔍 Key Insights", "💬 Ask Anything", "📊 Compare Documents", "📥 Export Report"]
tab1, tab2, tab3, tab4 = st.tabs(tabs)

# ── Tab 1: Key Insights ───────────────────────────────────────────────────────
with tab1:
    st.subheader("Key Information Extracted")
    st.caption("Automatically pulled from your document — explained in plain English.")

    if st.button("Extract Key Insights", type="primary"):
        with st.spinner("Extracting and simplifying..."):
            st.session_state.insights = extract_key_info(vectorstore, domain)

    if st.session_state.insights:
        for section, content in st.session_state.insights.items():
            with st.expander(f"📌 {section}", expanded=True):
                st.write(content)

# ── Tab 2: Q&A ────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Ask Anything About Your Document")
    st.caption("Ask in plain English. Answers include a confidence level.")

    if st.button("🗑️ Clear conversation", key="clear"):
        st.session_state.chat_history = []
        reset_memory()

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

# ── Tab 3: Compare ────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Compare Two Documents")
    st.caption("Upload a second PDF in the sidebar, then compare on any topic.")

    if not st.session_state.vectorstore_b:
        st.info("Upload a second PDF in the sidebar to enable comparison.")
    else:
        compare_topic = st.text_input(
            "What topic do you want to compare?",
            placeholder="e.g. Payment terms, penalties, termination conditions..."
        )
        if st.button("Compare Documents", type="primary") and compare_topic:
            with st.spinner("Comparing both documents..."):
                result = compare_documents(vectorstore, st.session_state.vectorstore_b, compare_topic)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**📄 {uploaded_file.name}**")
                st.info(result["doc_a_summary"])
            with col_b:
                st.markdown(f"**📄 {st.session_state.filename_b}**")
                st.info(result["doc_b_summary"])

            st.markdown("### 🔍 Comparison")
            st.write(result["comparison"])

# ── Tab 4: Export ─────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Export Analysis Report")
    st.caption("Download a PDF report with all insights and Q&A from this session.")

    if not st.session_state.insights and not st.session_state.chat_history:
        st.info("Extract insights or ask questions first — then export your report here.")
    else:
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Building your report..."):
                pdf_bytes = export_to_pdf(
                    filename=uploaded_file.name,
                    domain=domain,
                    insights=st.session_state.insights,
                    chat_history=st.session_state.chat_history,
                )
            st.download_button(
                label="📥 Download Report",
                data=pdf_bytes,
                file_name=f"docusense_report_{uploaded_file.name.replace('.pdf','')}.pdf",
                mime="application/pdf",
            )
            st.success("Report ready! Click the button above to download.")