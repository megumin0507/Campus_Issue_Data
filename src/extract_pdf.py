import pdfplumber
from pathlib import Path


def extract_pdf(pdf_path: Path) -> dict:
    pages = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []

            pages.append({
                "page_number": page_index,
                "text": text,
                "tables": tables,
            })

    full_text = "\n\n".join(page["text"] for page in pages)

    return {
        "metadata": {
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "page_count": len(pages),
        },
        "pages": pages,
        "text": full_text,
    }