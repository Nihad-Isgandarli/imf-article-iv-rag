"""Extract plain text from IMF Article IV PDF reports."""

from pathlib import Path
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file as a single string.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The full text content of the PDF, with pages separated by newlines.
    """
    reader = PdfReader(pdf_path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def main() -> None:
    """Quick test: extract text from turkey_2018.pdf and print summary."""
    pdf_path = Path("data/raw/turkey_2018.pdf")

    if not pdf_path.exists():
        print(f"ERROR: File not found at {pdf_path}")
        return

    print(f"Reading: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)

    
    print(f"\n--- Extraction summary ---")
    print(f"Total characters: {len(text):,}")
    print(f"Total words: {len(text.split()):,}")
    print(f"Total pages: {len(PdfReader(pdf_path).pages)}")

    
    print(f"\n--- First 500 characters ---")
    print(text[:500])


if __name__ == "__main__":
    main()