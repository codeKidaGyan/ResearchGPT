# ResearchGPT

ResearchGPT is a complete AI Scientific Research Assistant built fully in Python using Streamlit, Groq API, ChromaDB, PyPDF2, and SQLite.

## Features
- Local login/signup with SQLite authentication
- Dashboard with research activity overview
- PDF upload and text extraction
- Research paper summarization
- Chat with uploaded PDF using retrieval-augmented generation
- Research gap detection
- Citation generation in APA, IEEE, and MLA formats
- Saved chat history
- Export summaries as PDF
- Responsive and professional Streamlit UI

## Setup
1. Create a virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Copy `.env.example` to `.env` and add your Groq API key.
4. Run:
   streamlit run app.py

## Notes
- Uploaded PDFs are saved in `uploads/`.
- SQLite database is created in `data/researchgpt.db`.
- ChromaDB persistent store is created in `chroma_store/`.
