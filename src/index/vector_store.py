import numpy as np
import json
from pathlib import Path

class VectorStore:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.chunks = []
        self.vectors = None

    def build(self, chunks: list[dict]) -> None:
        
        if not isinstance(chunks, list):
            raise TypeError("chunks must be a list of dictionaries")
        if not chunks:
            raise ValueError("chunks must not be empty")
        for chunk in chunks:
            if not isinstance(chunk, dict):
                raise TypeError("each chunk must be a dictionary")
            if "text" not in chunk:
                raise ValueError("each chunk must contain a text field")
            if not chunk["text"]:
                raise ValueError("chunk text must not be empty")

        self.chunks = chunks

        texts = [chunk["text"] for chunk in chunks]
        self.vectors = np.array(self.embedding_model.encode(texts), dtype="float32")

    def search(self, query: str, top_k: int = 5) -> list[dict]:

        if self.vectors is None:
            raise ValueError("VectorStore has not been built yet")
        if not query:
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        query_vector = self.embedding_model.encode([query])[0]
        query_vector = np.array(query_vector, dtype="float32")

        scores = self.vectors @ query_vector

        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for index in top_indices:
            chunk = self.chunks[index].copy()
            chunk["score"] = float(scores[index])
            results.append(chunk)

        return results
    
    def save(self, path: str) -> None:
        if self.vectors is None:
            raise ValueError("VectorStore has not been built yet")

        index_dir = Path(path)
        index_dir.mkdir(parents=True, exist_ok=True)

        chunks_path = index_dir / "chunks.json"
        vectors_path = index_dir / "vectors.npy"

        with chunks_path.open("w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

        np.save(vectors_path, self.vectors)

    def load(self, path: str) -> None:
        index_dir = Path(path)
        chunks_path = index_dir / "chunks.json"
        vectors_path = index_dir / "vectors.npy"

        if not chunks_path.exists():
            raise FileNotFoundError(f"chunks file not found: {chunks_path}")

        if not vectors_path.exists():
         raise FileNotFoundError(f"vectors file not found: {vectors_path}")

        with chunks_path.open("r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.vectors = np.load(vectors_path).astype("float32")


def main() -> None:
    from src.embeddings.embedding_model import EmbeddingModel

    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")

    chunks = [
        {
            "chunk_id": "c1",
            "text": "deep learning for image classification",
            "source": "demo",
            "page": 1,
            "metadata": {},
        },
        {
            "chunk_id": "c2",
            "text": "coffee and tea are common drinks",
            "source": "demo",
            "page": 2,
            "metadata": {},
        },
        {
            "chunk_id": "c3",
            "text": "neural networks improve computer vision",
            "source": "demo",
            "page": 3,
            "metadata": {},
        },
    ]

    store = VectorStore(model)
    store.build(chunks)

    results = store.search("computer vision neural network", top_k=2)

    print("Search results:")
    for result in results:
        print(
            f"{result['chunk_id']} "
            f"score={result['score']:.4f} "
            f"page={result['page']} "
            f"text={result['text']}"
        )

    store.save("data/index/vector_store_demo")

    loaded_store = VectorStore(model)
    loaded_store.load("data/index/vector_store_demo")

    loaded_results = loaded_store.search("computer vision neural network", top_k=1)
    print("Loaded index top result:")
    print(loaded_results[0]["chunk_id"])


if __name__ == "__main__":
    main()