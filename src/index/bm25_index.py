import re
from rank_bm25 import BM25Okapi
import numpy as np
import json
from pathlib import Path

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())

class BM25Index:
    def __init__(self):
        self.chunks = []
        self.tokenized_corpus = []
        self.bm25 = None

    def build(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        self.tokenized_corpus = [tokenize(chunk["text"]) for chunk in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
    def search(self, query: str, top_k: int = 5) -> list[dict]:

        if self.bm25 is None:
            raise ValueError("BM25Index has not been built yet")
        if not query:
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for index in top_indices:
            chunk = self.chunks[index].copy()
            chunk["score"] = float(scores[index])
            results.append(chunk)
        return results
    
    def save(self, path: str) -> None:
        if self.bm25 is None:
            raise ValueError("BM25Index has not been built yet")

        index_dir = Path(path)
        index_dir.mkdir(parents=True, exist_ok=True)

        chunks_path = index_dir / "bm25_chunks.json"

        with chunks_path.open("w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        index_dir = Path(path)
        chunks_path = index_dir / "bm25_chunks.json"

        if not chunks_path.exists():
            raise FileNotFoundError(f"BM25 chunks file not found: {chunks_path}")

        with chunks_path.open("r", encoding="utf-8") as f:
            chunks = json.load(f)

        self.build(chunks)


def main() -> None:
    chunks = [
    {
        "chunk_id": "c1",
        "text": "fault diagnosis method for rotating machinery using deep learning",
        "source": "demo",
        "page": 1,
        "metadata": {},
    },
    {
        "chunk_id": "c2",
        "text": "coffee and tea are common drinks in daily life",
        "source": "demo",
        "page": 2,
        "metadata": {},
    },
    {
        "chunk_id": "c3",
        "text": "image classification with neural network and convolution model",
        "source": "demo",
        "page": 3,
        "metadata": {},
    },
    {
        "chunk_id": "c4",
        "text": "bearing fault detection experiment for industrial equipment",
        "source": "demo",
        "page": 4,
        "metadata": {},
    },
    {
        "chunk_id": "c5",
        "text": "weather forecast and city temperature prediction",
        "source": "demo",
        "page": 5,
        "metadata": {},
    },
    {
        "chunk_id": "c6",
        "text": "medical report generation from clinical notes",
        "source": "demo",
        "page": 6,
        "metadata": {},
    },
]

    index = BM25Index()
    index.build(chunks)

    results = index.search("fault diagnosis", top_k=3)

    print("BM25 results:")
    for result in results:
        print(
            f"{result['chunk_id']} "
            f"score={result['score']:.4f} "
            f"page={result['page']} "
            f"text={result['text']}"
        )

    index.save("data/index/bm25_demo")

    loaded = BM25Index()
    loaded.load("data/index/bm25_demo")
    loaded_results = loaded.search("fault diagnosis", top_k=1)

    print("Loaded BM25 top result:")
    if loaded_results:
        print(loaded_results[0]["chunk_id"])
    else:
        print("No result")  


if __name__ == "__main__":
    main()