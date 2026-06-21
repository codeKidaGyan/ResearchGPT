from pathlib import Path

from PyPDF2 import PdfReader

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_pdf(uploaded_file, user_id: int) -> str:
    user_dir = UPLOAD_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / uploaded_file.name
    with open(destination, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(destination)


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()