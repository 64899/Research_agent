#离线构建索引，负责把 PDF 变成可检索的索引
import argparse
from src.loaders.pdf_loader import load_pdf
from src.chunkers.fixed_chunker import chunk_documents
from src.embeddings.embedding_model import EmbeddingModel
from src.index.vector_store import VectorStore
from src.index.bm25_index import BM25Index

def main() -> None:
    parser = argparse.ArgumentParser(description="Build a vector index from a PDF.")
    parser.add_argument("--input", required=True, help="Path to the input PDF file.")
    parser.add_argument("--index_dir", required=True, help="Directory to save the index.")

    args = parser.parse_args()

    print(f"Input PDF: {args.input}")
    print(f"Index directory: {args.index_dir}")

    documents = load_pdf(args.input)
    print(f"Loaded documents: {len(documents)}")

    chunks = chunk_documents(documents, chunk_size=800, overlap=100)
    print(f"Created chunks: {len(chunks)}")

    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
    store = VectorStore(model)
    store.build(chunks)
    store.save(args.index_dir)

    bm25_index = BM25Index()
    bm25_index.build(chunks)
    bm25_index.save(args.index_dir)

    print(f"Saved dense and BM25 indexes to: {args.index_dir}")

if __name__ == "__main__":
    main()