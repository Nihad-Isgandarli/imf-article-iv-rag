"""Generate dense vector embeddings for text chunks using sentence-transformers."""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

from extractor import extract_text_from_pdf
from chunker import chunk_text



EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def load_embedding_model() -> SentenceTransformer:
    """Load the sentence-transformer embedding model.

    On first run, this downloads ~80MB to a local cache.
    On subsequent runs, it loads from cache instantly.

    Returns:
        A loaded SentenceTransformer model.
    """
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return model


def embed_chunks(chunks: list[str], model: SentenceTransformer) -> np.ndarray:
    """Convert a list of text chunks into a 2D array of embedding vectors.

    Args:
        chunks: List of text chunks to embed.
        model: A loaded SentenceTransformer model.

    Returns:
        A numpy array of shape (n_chunks, embedding_dim).
    """
    embeddings = model.encode(chunks, show_progress_bar=True)
    return embeddings


def main() -> None:
    """Quick test: extract, chunk, and embed Turkey 2018 PDF."""
    project_root = Path(__file__).resolve().parent.parent
    pdf_path = project_root / "data" / "raw" / "turkey_2018.pdf"

    if not pdf_path.exists():
        print(f"ERROR: File not found at {pdf_path}")
        return

    
    print("Step 1: Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    print(f"  Extracted {len(text.split()):,} words")

    
    print("\nStep 2: Chunking text...")
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    print(f"  Created {len(chunks)} chunks")

    
    print("\nStep 3: Loading embedding model...")
    model = load_embedding_model()

    # 4. Generate embeddings
    print("\nStep 4: Generating embeddings...")
    embeddings = embed_chunks(chunks, model)

   
    print(f"\n--- Embedding summary ---")
    print(f"Number of vectors: {embeddings.shape[0]}")
    print(f"Vector dimension: {embeddings.shape[1]}")
    print(f"Memory size: {embeddings.nbytes / 1024:.1f} KB")
    print(f"\nFirst vector (first 8 dimensions): {embeddings[0][:8]}")


if __name__ == "__main__":
    main()