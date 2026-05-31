"""Build a ChromaDB vector store from IMF Article IV PDF reports.

For every PDF in data/raw/, this script extracts the text, splits it into
chunks, embeds them, and stores them in a persistent ChromaDB collection
with metadata (country, year) so we can later query a specific report.
"""

from pathlib import Path

import chromadb

from extractor import extract_text_from_pdf
from chunker import chunk_text
from embedder import load_embedding_model, embed_chunks

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PDF_DIR = PROJECT_ROOT / "data" / "raw"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "imf_article_iv"

def parse_filename(pdf_path: Path) -> tuple[str, int]:
    """Extract country and year from a filename like 'turkey_2016.pdf'.

    The year is always the last underscore-separated part. Everything
    before it is the country (which may itself contain underscores,
    e.g. 'sri_lanka_2021.pdf').

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A tuple (country, year), e.g. ("sri_lanka", 2021).
    """
    stem = pdf_path.stem               # "turkey_2016" (filename without .pdf)
    parts = stem.split("_")            # ["turkey", "2016"]
    year = int(parts[-1])              # last part → year as integer
    country = "_".join(parts[:-1])     # everything before → country
    return country, year

def process_pdf(pdf_path: Path, collection, model) -> int:
    """Extract, chunk, embed one PDF and add all chunks to ChromaDB.

    Args:
        pdf_path: Path to the PDF file.
        collection: The ChromaDB collection to add chunks to.
        model: The loaded embedding model.

    Returns:
        The number of chunks added for this PDF.
    """
    country, year = parse_filename(pdf_path)
    print(f"  Processing {country} {year}...")

    # 1. Extract text and split into chunks
    text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(text, chunk_size=500, overlap=50)

    # 2. Turn each chunk into a vector
    embeddings = embed_chunks(chunks, model)

    # 3. Build the metadata and unique IDs for each chunk
    ids = []
    metadatas = []
    for chunk_index in range(len(chunks)):
        ids.append(f"{country}_{year}_chunk{chunk_index}")
        metadatas.append({
            "country": country,
            "year": year,
            "chunk_id": chunk_index,
            "source_pdf": pdf_path.name,
        })

    # 4. Store everything in ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=chunks,
        metadatas=metadatas,
    )

    return len(chunks)

def main() -> None:
    """Build the full vector store from all PDFs in data/raw/."""

    # 1. Connect to ChromaDB (creates the folder if it doesn't exist)
    print(f"Opening ChromaDB at: {CHROMA_DB_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    # Start fresh: remove the collection if it already exists, then recreate
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Removed existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # 2. Load the embedding model once (reused for every PDF)
    model = load_embedding_model()

    # 3. Find all PDFs and process them one by one
    pdf_files = sorted(RAW_PDF_DIR.glob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDFs to process.\n")

    total_chunks = 0
    for pdf_path in pdf_files:
        chunks_added = process_pdf(pdf_path, collection, model)
        total_chunks += chunks_added

    # 4. Final summary
    print(f"\n--- Done ---")
    print(f"Processed {len(pdf_files)} PDFs")
    print(f"Total chunks stored: {total_chunks}")
    print(f"Collection '{COLLECTION_NAME}' saved in {CHROMA_DB_DIR}")


if __name__ == "__main__":
    main()
