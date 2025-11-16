import os
from PyPDF2 import PdfReader
from chatbot_backend import ask_ai  # reuse your Gemini helper


def extract_pdf_text(path: str) -> str:
    """Extract raw text from a PDF file."""
    if not os.path.exists(path):
        return ""
    try:
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
        return "\n".join(parts)
    except Exception:
        return ""


def summarize_pdf(path: str) -> str | None:
    """
    Use AI to summarize the PDF for students.
    Returns None if extraction fails.
    """
    text = extract_pdf_text(path)
    if not text.strip():
        return None

    # Avoid sending huge texts; truncate for safety
    short_text = text[:8000]

    prompt = (
        "You are a helpful teaching assistant. Read the following study material "
        "and create a short summary with:\n"
        "1. A 3-5 line overview\n"
        "2. 3-6 key bullet points\n"
        "3. Difficulty level (Beginner / Intermediate / Advanced)\n\n"
        f"CONTENT:\n{short_text}"
    )

    answer = ask_ai(prompt)
    return answer
