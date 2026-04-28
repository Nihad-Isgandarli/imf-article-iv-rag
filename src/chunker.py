"""Split extracted text into overlapping chunks for embedding."""

from pathlib import Path
from extractor import extract_text_from_pdf


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping word-based chunks.

    Args:
        text: The input text to chunk.
        chunk_size: Target number of words per chunk.
        overlap: Number of words to overlap between consecutive chunks.

    Returns:
        List of text chunks, each approximately chunk_size words long.
    """
    words = text.split()
    chunks: list[str] = []
    step = chunk_size - overlap

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)

        
        if i + chunk_size >= len(words):
            break

    return chunks


def main() -> None:
    """Quick test: extract Turkey 2018 PDF and chunk it."""
    pdf_path = Path("data/raw/turkey_2018.pdf")

    if not pdf_path.exists():
        print(f"ERROR: File not found at {pdf_path}")
        return

    print(f"Reading: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    print(f"Total words: {len(text.split()):,}")

    chunks = chunk_text(text, chunk_size=500, overlap=50)

    print(f"\n--- Chunking summary ---")
    print(f"Total chunks: {len(chunks)}")
    print(f"Average chunk size: {sum(len(c.split()) for c in chunks) / len(chunks):.0f} words")

    
    if len(chunks) >= 5:
        print(f"\n--- Sample: Chunk #5 (first 300 chars) ---")
        print(chunks[4][:300])
        print("...")


if __name__ == "__main__":
    main()