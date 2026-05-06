from pathlib import Path
from pypdf import PdfReader


def extract_pdf(pdf_path: Path) -> dict:
    """
    Extract text and basic metadata from a PDF file.

    Returns:
        {
            "metadata": {
                "filename": "...",
                "file_path": "...",
                "page_count": ...
            },
            "pages": [
                {
                    "page_number": 1,
                    "text": "..."
                }
            ],
            "text": "full document text..."
        }
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))

    pages = []

    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()

        if page_text is None:
            page_text = ""

        pages.append(
            {
                "page_number": index,
                "text": page_text,
            }
        )

    full_text = "\n\n".join(page["text"] for page in pages)

    return {
        "metadata": {
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "page_count": len(reader.pages),
        },
        "pages": pages,
        "text": full_text,
    }