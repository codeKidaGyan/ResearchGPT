import os
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from auth import login_user, signup_user
from citation_generator import generate_citation
from database import (
    get_chat_history,
    get_uploaded_papers,
    init_db,
    save_chat_message,
    save_summary,
    save_uploaded_paper,
)
from export_pdf import export_text_to_pdf
from pdf_processor import extract_text_from_pdf, save_uploaded_pdf
from rag_engine import ResearchAssistant
import auth
print(auth.__file__)


load_dotenv()
init_db()

st.set_page_config(
    page_title="ResearchGPT",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
:root {
    --primary: #0f766e;
    --primary-dark: #115e59;
    --secondary: #0f172a;
    --bg: #f8fafc;
    --card: #ffffff;
    --muted: #64748b;
    --border: #e2e8f0;
    --accent: #14b8a6;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f8fafc 0%, #eef6ff 100%);
    color: #0f172a;
}

[data-testid="stSidebar"] {
    background: #0f172a;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.block-container {
    padding-top: 1.3rem;
    padding-bottom: 2rem;
}

.research-card {
    background: var(--card);
    color: #0f172a;
    padding: 1.2rem;
    border-radius: 18px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    margin-bottom: 1rem;
}

.metric-card {
    background: linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%);
    color: #0f172a;
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid #ccfbf1;
    box-shadow: 0 8px 20px rgba(20, 184, 166, 0.08);
}

.metric-card h3,
.metric-card p {
    color: #0f172a !important;
}

.hero {
    padding: 1.4rem;
    border-radius: 24px;
    background: linear-gradient(120deg, #0f172a 0%, #134e4a 100%);
    color: white;
    margin-bottom: 1rem;
}

.hero * {
    color: white !important;
}

.small-muted {
    color: #64748b !important;
    font-size: 0.95rem;
}

.chat-box {
    border-radius: 14px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border);
    color: #0f172a;
}

.user-msg {
    background: #ecfeff;
    color: #0f172a;
}

.assistant-msg {
    background: #0f172a;
    color: white !important;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid #0f766e;
    background: #0f766e;
    color: white !important;
    font-weight: 600;
}

.stButton > button:hover {
    background: #115e59;
    color: white !important;
}

/* Fix invisible Streamlit text */
p, div, span, label {
    color: #0f172a !important;
}

.stTextInput label,
.stTextArea label,
.stSelectbox label {
    color: #0f172a !important;
    font-weight: 600;
}

.stTabs [data-baseweb="tab"] {
    color: #334155 !important;
}

.stTabs [aria-selected="true"] {
    color: #0f766e !important;
    font-weight: 700;
}
/* Streamlit Selectbox Fix */

div[data-baseweb="select"] {
    background-color: white !important;
}

div[data-baseweb="select"] * {
    color: black !important;
}

/* Dropdown popup */
ul[role="listbox"] {
    background-color: white !important;
}

li[role="option"] {
    background-color: white !important;
    color: black !important;
}

li[role="option"]:hover {
    background-color: #e5e7eb !important;
    color: black !important;
}
/* Sidebar selectbox */
[data-testid="stSidebar"] div[data-baseweb="select"] {
    background: white !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #0f172a !important;
}

[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #0f172a !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None
if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "selected_paper_id" not in st.session_state:
    st.session_state.selected_paper_id = None
if "selected_paper_name" not in st.session_state:
    st.session_state.selected_paper_name = None
if "selected_paper_text" not in st.session_state:
    st.session_state.selected_paper_text = ""
if "last_summary" not in st.session_state:
    st.session_state.last_summary = ""
if "last_gaps" not in st.session_state:
    st.session_state.last_gaps = ""
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

def reset_paper_state():
    st.session_state.selected_paper_id = None
    st.session_state.selected_paper_name = None
    st.session_state.selected_paper_text = ""


def ensure_assistant():
    if st.session_state.assistant is None:
        st.session_state.assistant = ResearchAssistant()
    return st.session_state.assistant


def auth_screen():
    st.markdown(
        """
        <div class='hero'>
            <h1 style='margin-bottom:0.3rem;'>ResearchGPT</h1>
            <p style='margin:0;'>AI Scientific Research Assistant for summarization, paper chat, research gap analysis, and citation creation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("### Features")
        st.markdown(
            """
- Local login/signup with SQLite
- Upload and analyze research PDFs
- AI summaries using Groq
- Ask questions about uploaded papers
- Detect research gaps and future directions
- Generate APA, IEEE, and MLA citations
- Save complete chat history
- Export summaries to PDF
            """
        )
    with right:
        st.markdown("<div class='research-card'>", unsafe_allow_html=True)
        mode = st.radio("Access", ["login", "signup"], index=0 if st.session_state.auth_mode == "login" else 1, horizontal=True)
        st.session_state.auth_mode = mode
        username = st.text_input("Username", key="auth_username")
        password = st.text_input("Password", type="password", key="auth_password")
        if mode == "signup":
            confirm_password = st.text_input("Confirm Password", type="password", key="auth_confirm_password")
            if st.button("Create Account", use_container_width=True):
                if not username or not password:
                    st.error("Username and password are required.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = signup_user(username, password)
                    if success:
                        st.success(message)
                        st.session_state.auth_mode = "login"
                    else:
                        st.error(message)
        else:
            if st.button("Login", use_container_width=True):
                success, user = login_user(username, password)
                if success:
                    st.session_state.user = user
                    st.session_state.assistant = ResearchAssistant()
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.markdown("</div>", unsafe_allow_html=True)


def sidebar_panel(user):
    with st.sidebar:
        st.markdown(f"## Welcome, {user['username']}")
        st.caption("Research workspace")
        papers = get_uploaded_papers(user["id"])
        paper_names = [f"{paper['id']} · {paper['file_name']}" for paper in papers]
        selected_label = st.selectbox("Your uploaded papers", ["None"] + paper_names)
        if selected_label != "None":
            paper_id = int(selected_label.split("·")[0].strip())
            selected_paper = next((p for p in papers if p["id"] == paper_id), None)
            if selected_paper:
                st.session_state.selected_paper_id = selected_paper["id"]
                st.session_state.selected_paper_name = selected_paper["file_name"]
                st.session_state.selected_paper_text = selected_paper["content"]
        else:
            reset_paper_state()

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.assistant = None
            reset_paper_state()
            st.rerun()


def dashboard(user):
    papers = get_uploaded_papers(user["id"])
    history = get_chat_history(user["id"], limit=1000)
    summaries = sum(1 for item in history if item["message_type"] == "summary")

    st.markdown(
        f"""
        <div class='hero'>
            <h1 style='margin-bottom:0.35rem;'>ResearchGPT Dashboard</h1>
            <p style='margin:0;'>Upload papers, generate summaries, find research gaps, and chat with your documents from one workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h3>{len(papers)}</h3><p class='small-muted'>Uploaded Papers</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h3>{len(history)}</h3><p class='small-muted'>Saved Interactions</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h3>{summaries}</h3><p class='small-muted'>Generated Summaries</p></div>", unsafe_allow_html=True)


def upload_section(user):
    st.markdown("## PDF Upload")
    uploaded_file = st.file_uploader("Upload a research paper in PDF format", type=["pdf"])
    if uploaded_file and st.button("Process PDF", use_container_width=True):
        with st.spinner("Reading and storing PDF..."):
            file_path = save_uploaded_pdf(uploaded_file, user["id"])
            text = extract_text_from_pdf(file_path)
            if not text.strip():
                st.error("No readable text found in the PDF.")
                return
            paper_id = save_uploaded_paper(user["id"], uploaded_file.name, text, file_path)
            st.session_state.selected_paper_id = paper_id
            st.session_state.selected_paper_name = uploaded_file.name
            st.session_state.selected_paper_text = text
            ensure_assistant().index_document(str(paper_id), text, {"file_name": uploaded_file.name, "user_id": user["id"]})
            st.success(f"PDF processed successfully: {uploaded_file.name}")


def summarize_section(user):
    st.markdown("## Paper Summary")
    if not st.session_state.selected_paper_text:
        st.info("Select or upload a paper to generate its summary.")
        return

    summary_style = st.selectbox("Summary style", ["Concise", "Detailed", "Bullet Points", "Methodology Focus"])
    if st.button("Generate Summary", use_container_width=True):
        with st.spinner("Generating summary..."):
            assistant = ensure_assistant()
            summary = assistant.summarize_document(st.session_state.selected_paper_text, summary_style)
            st.session_state.last_summary = summary
            save_summary(user["id"], st.session_state.selected_paper_id, summary, summary_style)
            save_chat_message(user["id"], st.session_state.selected_paper_id, "summary", f"Summary ({summary_style})", summary)

    if st.session_state.last_summary:
        st.markdown("<div class='research-card'>", unsafe_allow_html=True)
        st.write(st.session_state.last_summary)
        pdf_bytes = export_text_to_pdf(
            title=f"Summary - {st.session_state.selected_paper_name or 'Research Paper'}",
            body=st.session_state.last_summary,
        )
        st.download_button(
            "Export Summary as PDF",
            data=pdf_bytes,
            file_name="research_summary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def gap_section(user):
    st.markdown("## Research Gap Detection")
    if not st.session_state.selected_paper_text:
        st.info("Upload or select a paper first.")
        return

    if st.button("Detect Research Gaps", use_container_width=True):
        with st.spinner("Analyzing gaps and future work opportunities..."):
            assistant = ensure_assistant()
            gaps = assistant.detect_research_gaps(st.session_state.selected_paper_text)
            st.session_state.last_gaps = gaps
            save_chat_message(user["id"], st.session_state.selected_paper_id, "gap_analysis", "Research gap analysis", gaps)

    if st.session_state.last_gaps:
        st.markdown("<div class='research-card'>", unsafe_allow_html=True)
        st.write(st.session_state.last_gaps)
        st.markdown("</div>", unsafe_allow_html=True)


def citation_section():
    st.markdown("## Citation Generator")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Paper Title")
        authors = st.text_input("Authors (comma separated)")
        year = st.text_input("Year")
        journal = st.text_input("Journal / Conference")
    with col2:
        volume = st.text_input("Volume")
        issue = st.text_input("Issue")
        pages = st.text_input("Pages")
        doi = st.text_input("DOI or URL")

    style = st.selectbox("Citation style", ["APA", "IEEE", "MLA"])
    if st.button("Generate Citation", use_container_width=True):
        citation = generate_citation(
            style=style,
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi,
        )
        st.code(citation)


def chat_section(user):
    st.markdown("## Chat with PDF")
    if not st.session_state.selected_paper_text:
        st.info("Select or upload a paper to start chatting.")
        return

    assistant = ensure_assistant()
    chat_history = get_chat_history(user["id"], st.session_state.selected_paper_id, limit=50)
    for item in chat_history:
        if item["message_type"] in {"user", "assistant"}:
            css_class = "user-msg" if item["message_type"] == "user" else "assistant-msg"
            role = "You" if item["message_type"] == "user" else "ResearchGPT"
            st.markdown(f"<div class='chat-box {css_class}'><strong>{role}:</strong><br>{item['response']}</div>", unsafe_allow_html=True)

    question = st.text_input("Ask something about the selected paper", key="chat_question")
    if st.button("Send Question", use_container_width=True):
        if not question.strip():
            st.warning("Enter a question first.")
            return
        with st.spinner("Thinking..."):
            answer = assistant.answer_question(
                document_id=str(st.session_state.selected_paper_id),
                document_text=st.session_state.selected_paper_text,
                question=question,
            )
            save_chat_message(user["id"], st.session_state.selected_paper_id, "user", question, question)
            save_chat_message(user["id"], st.session_state.selected_paper_id, "assistant", question, answer)
            st.rerun()


def history_section(user):
    st.markdown("## Saved Chat History")
    history = get_chat_history(user["id"], st.session_state.selected_paper_id, limit=100)
    if not history:
        st.info("No saved history yet.")
        return

    for item in history:
        timestamp = item["created_at"]
        st.markdown("<div class='research-card'>", unsafe_allow_html=True)
        st.write(f"**Type:** {item['message_type']}  ")
        st.write(f"**Prompt:** {item['prompt']}  ")
        st.write(f"**Response:** {item['response']}  ")
        st.caption(f"Saved at: {timestamp}")
        st.markdown("</div>", unsafe_allow_html=True)


if st.session_state.user is None:
    auth_screen()
else:
    user = st.session_state.user
    sidebar_panel(user)
    dashboard(user)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Upload PDF", "Summarize", "Chat", "Research Gaps", "Citations", "History"]
    )

    with tab1:
        upload_section(user)
    with tab2:
        summarize_section(user)
    with tab3:
        chat_section(user)
    with tab4:
        gap_section(user)
    with tab5:
        citation_section()
    with tab6:
        history_section(user)
